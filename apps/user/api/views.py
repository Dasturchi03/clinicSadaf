from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.db.models import Prefetch, Q
from rest_framework import generics, status
from rest_framework.decorators import api_view, action
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.api.views import BaseViewSet
from apps.core.pagination import BasePagination
from apps.core.permissions import AccessPermissions
from apps.user import filtersets
from apps.user.api import serializers
from apps.user.models import User, User_Type, UserSalary, UserSchedule
from apps.user.permissions import UserPermissions


class LoginView(TokenObtainPairView):
    serializer_class = serializers.LoginSerializer


class UserViewSet(BaseViewSet):
    pagination_class = BasePagination
    filterset_class = filtersets.UserFilterSet
    permission_classes = (AccessPermissions,)
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.UserListSerializer
        if self.action == "create":
            return serializers.UserSerializer
        if self.action == "retrieve":
            return serializers.UserSerializerData
        if self.action == "partial_update":
            return serializers.UserSerializerData

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_user"] = self.request.user
        return context

    def get_queryset(self):
        queryset = (
            User.objects.select_related("user_type")
            .prefetch_related(
                "user_public_phone",
                "user_private_phone",
                "groups",
                "user_permissions",
                "user_schedule",
            )
            .exclude(
                Q(user_type=None)
                | Q(is_superuser=True)
                | Q(user_type__type_text="Пациент")
            )
        )
        if self.action == "list":
            queryset = (
                User.objects.select_related("user_type")
                .prefetch_related(
                    "user_public_phone", "user_private_phone", "user_specialization"
                )
                .only("id", "user_firstname", "user_lastname", "user_type_id")
                .exclude(
                    Q(user_type=None)
                    | Q(is_superuser=True)
                    | Q(user_type__type_text="Пациент")
                )
            )

        if self.request.query_params:
            return super().filter_queryset(queryset)

        return queryset


class DoctorsApiView(generics.ListAPIView):
    filterset_class = filtersets.DoctorsFilterSet
    permission_classes = (AccessPermissions,)
    serializer_class = serializers.DoctorsListSerializer

    def get_queryset(self):
        return (
            User.objects
            .select_related("user_type")
            .prefetch_related("user_public_phone", "user_private_phone", "user_specialization")
            .only("id", "user_firstname", "user_lastname", "user_type_id", "user_image")
            .filter(
                user_is_active=True,
                archive=False,
                deleted=False,
                user_type__type_text='Доктор'
            )
        )


class UserUploadImageView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = serializers.UserImageSerializer
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            user_instance = self.queryset.get(pk=data["id"])
            image = self.request.FILES["user_image"]
            user_instance.user_image.save(image.name, image)
            data = {"Image uploaded successfully"}
            return Response(data, status=status.HTTP_200_OK)
        except:
            data = {"Oops something went wrong"}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class UserBriefListView(generics.ListAPIView):
    queryset = User.objects.only(
        "id", "user_firstname", "user_lastname", "user_father_name", "user_color"
    ).exclude(
        Q(user_type=None) | Q(is_superuser=True) | Q(user_type__type_text="Пациент")
    )
    filterset_class = filtersets.UserFilterSet
    serializer_class = serializers.UserBriefListSerializer
    permission_classes = (AccessPermissions,)


class UserSchduleListView(generics.ListAPIView):
    queryset = (
        User.objects.prefetch_related(
            Prefetch(
                lookup="user_schedule",
                queryset=UserSchedule.objects.only(
                    "user_id",
                    "day",
                    "work_start_time",
                    "work_end_time",
                    "lunch_start_time",
                    "lunch_end_time",
                    "is_working",
                ),
            )
        )
        .only("id", "user_firstname", "user_lastname", "user_father_name", "user_color")
        .exclude(
            Q(user_type=None) | Q(is_superuser=True) | Q(user_type__type_text="Пациент")
        )
    )
    filterset_class = filtersets.UserFilterSet
    serializer_class = serializers.UserScheduleListSerializer
    permission_classes = (AccessPermissions,)


class UserTypeViewSet(BaseViewSet):
    queryset = User_Type.objects.exclude(type_text="Пациент")
    serializer_class = serializers.UserTypeSerializer
    permission_classes = (AccessPermissions,)

    def destroy(self, request, *args, **kwargs):
        """Endpoint for deleting user type"""

        try:
            instance = self.get_object()
            users = []
            x = ", "
            connected_users = User.objects.filter(user_type_id=instance.pk)
            for index in connected_users:
                users.append(index.user_firstname + " " + index.user_lastname)
            if connected_users.exists():
                data = {
                    "Error": "Sorry we have connected users ({}) to this user type ({})".format(
                        x.join(users), instance
                    )
                }
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
            else:
                instance.delete()
                data = {"User type deleted successfully"}
                return Response(data, status=status.HTTP_200_OK)
        except:
            data = {"Oops something went wrong"}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class UserPasswordUpdateView(GenericAPIView):
    """Endpoint for updating password of user, current user has permission to change its own password, if it is admin user with permission, it can change any password"""

    queryset = User.objects.all()
    serializer_class = serializers.UserPasswordUpdateSerializer
    permission_classes = (AccessPermissions,)

    def get_object(self, *args, **kwargs):
        obj = self.queryset.get(pk=self.kwargs.get("pk"))
        return obj

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        current_user = request.user
        serializer = self.serializer_class(
            instance, data=request.data, context={"current_user": current_user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        message = ["Password updated successfully"]
        return Response(message, status=status.HTTP_200_OK)


class UserPermissionList(GenericAPIView):
    """Endpoint for list of user's permissions"""

    queryset = User.objects.all()
    serializer_class = serializers.UserPermissionsSerializer
    permission_classes = (UserPermissions,)

    def get_object(self, *args, **kwargs):
        queryset = self.queryset
        obj = queryset.get(pk=self.kwargs.get("pk"))
        return obj

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, context={"user": instance})
        return Response(serializer.data)


class GroupListView(ListAPIView):
    """Endpoint for list of groups"""

    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = (AccessPermissions,)

    def get_queryset(self):
        return self.queryset.all().exclude(name="Пациент")


class PermissionGroupListView(ListAPIView):
    """Endpoint for list of group's permissions"""

    queryset = Permission.objects.all()
    serializer_class = serializers.PermissionSerializer
    permission_classes = (AccessPermissions,)

    def get_queryset(self, *args, **kwargs):
        return self.queryset.filter(group__id=self.kwargs.get("group_id"))


class PermissionAllListView(ListAPIView):
    """Endpoint for list of all permissions"""

    serializer_class = serializers.PermissionSerializer

    def get_queryset(self):
        # Dynamically get all installed app labels except Django system apps
        registered_apps = [
            app.label for app in apps.get_app_configs() if app.name.startswith("apps")
        ]
        return Permission.objects.filter(content_type__app_label__in=registered_apps)


class UserSalaryViewSet(BaseViewSet):
    pagination_class = BasePagination
    permission_classes = (AccessPermissions,)
    filterset_class = filtersets.UserSalaryFilter
    http_method_names = ["get", "delete", "patch", "put"]
    lookup_field = "salary_id"

    def get_queryset(self):
        if self.action == "list":
            user_id = self.kwargs.get("user_id")
            queryset = UserSalary.objects.filter(salary_for_user_id=user_id)
        else:
            queryset = UserSalary.objects.all()
        if self.request.query_params:
            return super().filter_queryset(queryset)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["current_user"] = self.request.user
        return context

    def get_serializer_class(self):
        if self.action in ["list", "get"]:
            return serializers.UserSalarySerializer
        return serializers.UserSalaryUpdateSerializer


@api_view(["GET"])
def CountryListView(request):
    if request.LANGUAGE_CODE == "en":
        data = [
            {"name": "Afghanistan", "code": "AF"},
            {"name": "land Islands", "code": "AX"},
            {"name": "Albania", "code": "AL"},
            {"name": "Algeria", "code": "DZ"},
            {"name": "American Samoa", "code": "AS"},
            {"name": "AndorrA", "code": "AD"},
            {"name": "Angola", "code": "AO"},
            {"name": "Anguilla", "code": "AI"},
            {"name": "Antarctica", "code": "AQ"},
            {"name": "Antigua and Barbuda", "code": "AG"},
            {"name": "Argentina", "code": "AR"},
            {"name": "Armenia", "code": "AM"},
            {"name": "Aruba", "code": "AW"},
            {"name": "Australia", "code": "AU"},
            {"name": "Austria", "code": "AT"},
            {"name": "Azerbaijan", "code": "AZ"},
            {"name": "Bahamas", "code": "BS"},
            {"name": "Bahrain", "code": "BH"},
            {"name": "Bangladesh", "code": "BD"},
            {"name": "Barbados", "code": "BB"},
            {"name": "Belarus", "code": "BY"},
            {"name": "Belgium", "code": "BE"},
            {"name": "Belize", "code": "BZ"},
            {"name": "Benin", "code": "BJ"},
            {"name": "Bermuda", "code": "BM"},
            {"name": "Bhutan", "code": "BT"},
            {"name": "Bolivia", "code": "BO"},
            {"name": "Bosnia and Herzegovina", "code": "BA"},
            {"name": "Botswana", "code": "BW"},
            {"name": "Bouvet Island", "code": "BV"},
            {"name": "Brazil", "code": "BR"},
            {"name": "British Indian Ocean Territory", "code": "IO"},
            {"name": "Brunei Darussalam", "code": "BN"},
            {"name": "Bulgaria", "code": "BG"},
            {"name": "Burkina Faso", "code": "BF"},
            {"name": "Burundi", "code": "BI"},
            {"name": "Cambodia", "code": "KH"},
            {"name": "Cameroon", "code": "CM"},
            {"name": "Canada", "code": "CA"},
            {"name": "Cape Verde", "code": "CV"},
            {"name": "Cayman Islands", "code": "KY"},
            {"name": "Central African Republic", "code": "CF"},
            {"name": "Chad", "code": "TD"},
            {"name": "Chile", "code": "CL"},
            {"name": "China", "code": "CN"},
            {"name": "Christmas Island", "code": "CX"},
            {"name": "Cocos (Keeling) Islands", "code": "CC"},
            {"name": "Colombia", "code": "CO"},
            {"name": "Comoros", "code": "KM"},
            {"name": "Congo", "code": "CG"},
            {"name": "Congo, The Democratic Republic of the", "code": "CD"},
            {"name": "Cook Islands", "code": "CK"},
            {"name": "Costa Rica", "code": "CR"},
            {"name": 'Cote D"Ivoire', "code": "CI"},
            {"name": "Croatia", "code": "HR"},
            {"name": "Cuba", "code": "CU"},
            {"name": "Cyprus", "code": "CY"},
            {"name": "Czech Republic", "code": "CZ"},
            {"name": "Denmark", "code": "DK"},
            {"name": "Djibouti", "code": "DJ"},
            {"name": "Dominica", "code": "DM"},
            {"name": "Dominican Republic", "code": "DO"},
            {"name": "Ecuador", "code": "EC"},
            {"name": "Egypt", "code": "EG"},
            {"name": "El Salvador", "code": "SV"},
            {"name": "Equatorial Guinea", "code": "GQ"},
            {"name": "Eritrea", "code": "ER"},
            {"name": "Estonia", "code": "EE"},
            {"name": "Ethiopia", "code": "ET"},
            {"name": "Falkland Islands (Malvinas)", "code": "FK"},
            {"name": "Faroe Islands", "code": "FO"},
            {"name": "Fiji", "code": "FJ"},
            {"name": "Finland", "code": "FI"},
            {"name": "France", "code": "FR"},
            {"name": "French Guiana", "code": "GF"},
            {"name": "French Polynesia", "code": "PF"},
            {"name": "French Southern Territories", "code": "TF"},
            {"name": "Gabon", "code": "GA"},
            {"name": "Gambia", "code": "GM"},
            {"name": "Georgia", "code": "GE"},
            {"name": "Germany", "code": "DE"},
            {"name": "Ghana", "code": "GH"},
            {"name": "Gibraltar", "code": "GI"},
            {"name": "Greece", "code": "GR"},
            {"name": "Greenland", "code": "GL"},
            {"name": "Grenada", "code": "GD"},
            {"name": "Guadeloupe", "code": "GP"},
            {"name": "Guam", "code": "GU"},
            {"name": "Guatemala", "code": "GT"},
            {"name": "Guernsey", "code": "GG"},
            {"name": "Guinea", "code": "GN"},
            {"name": "Guinea-Bissau", "code": "GW"},
            {"name": "Guyana", "code": "GY"},
            {"name": "Haiti", "code": "HT"},
            {"name": "Heard Island and Mcdonald Islands", "code": "HM"},
            {"name": "Holy See (Vatican City State)", "code": "VA"},
            {"name": "Honduras", "code": "HN"},
            {"name": "Hong Kong", "code": "HK"},
            {"name": "Hungary", "code": "HU"},
            {"name": "Iceland", "code": "IS"},
            {"name": "India", "code": "IN"},
            {"name": "Indonesia", "code": "ID"},
            {"name": "Iran, Islamic Republic Of", "code": "IR"},
            {"name": "Iraq", "code": "IQ"},
            {"name": "Ireland", "code": "IE"},
            {"name": "Isle of Man", "code": "IM"},
            {"name": "Israel", "code": "IL"},
            {"name": "Italy", "code": "IT"},
            {"name": "Jamaica", "code": "JM"},
            {"name": "Japan", "code": "JP"},
            {"name": "Jersey", "code": "JE"},
            {"name": "Jordan", "code": "JO"},
            {"name": "Kazakhstan", "code": "KZ"},
            {"name": "Kenya", "code": "KE"},
            {"name": "Kiribati", "code": "KI"},
            {"name": 'Korea, Democratic People"S Republic of', "code": "KP"},
            {"name": "Korea, Republic of", "code": "KR"},
            {"name": "Kuwait", "code": "KW"},
            {"name": "Kyrgyzstan", "code": "KG"},
            {"name": 'Lao People"S Democratic Republic', "code": "LA"},
            {"name": "Latvia", "code": "LV"},
            {"name": "Lebanon", "code": "LB"},
            {"name": "Lesotho", "code": "LS"},
            {"name": "Liberia", "code": "LR"},
            {"name": "Libyan Arab Jamahiriya", "code": "LY"},
            {"name": "Liechtenstein", "code": "LI"},
            {"name": "Lithuania", "code": "LT"},
            {"name": "Luxembourg", "code": "LU"},
            {"name": "Macao", "code": "MO"},
            {"name": "Macedonia, The Former Yugoslav Republic of", "code": "MK"},
            {"name": "Madagascar", "code": "MG"},
            {"name": "Malawi", "code": "MW"},
            {"name": "Malaysia", "code": "MY"},
            {"name": "Maldives", "code": "MV"},
            {"name": "Mali", "code": "ML"},
            {"name": "Malta", "code": "MT"},
            {"name": "Marshall Islands", "code": "MH"},
            {"name": "Martinique", "code": "MQ"},
            {"name": "Mauritania", "code": "MR"},
            {"name": "Mauritius", "code": "MU"},
            {"name": "Mayotte", "code": "YT"},
            {"name": "Mexico", "code": "MX"},
            {"name": "Micronesia, Federated States of", "code": "FM"},
            {"name": "Moldova, Republic of", "code": "MD"},
            {"name": "Monaco", "code": "MC"},
            {"name": "Mongolia", "code": "MN"},
            {"name": "Montenegro", "code": "ME"},
            {"name": "Montserrat", "code": "MS"},
            {"name": "Morocco", "code": "MA"},
            {"name": "Mozambique", "code": "MZ"},
            {"name": "Myanmar", "code": "MM"},
            {"name": "Namibia", "code": "NA"},
            {"name": "Nauru", "code": "NR"},
            {"name": "Nepal", "code": "NP"},
            {"name": "Netherlands", "code": "NL"},
            {"name": "Netherlands Antilles", "code": "AN"},
            {"name": "New Caledonia", "code": "NC"},
            {"name": "New Zealand", "code": "NZ"},
            {"name": "Nicaragua", "code": "NI"},
            {"name": "Niger", "code": "NE"},
            {"name": "Nigeria", "code": "NG"},
            {"name": "Niue", "code": "NU"},
            {"name": "Norfolk Island", "code": "NF"},
            {"name": "Northern Mariana Islands", "code": "MP"},
            {"name": "Norway", "code": "NO"},
            {"name": "Oman", "code": "OM"},
            {"name": "Pakistan", "code": "PK"},
            {"name": "Palau", "code": "PW"},
            {"name": "Palestinian Territory, Occupied", "code": "PS"},
            {"name": "Panama", "code": "PA"},
            {"name": "Papua New Guinea", "code": "PG"},
            {"name": "Paraguay", "code": "PY"},
            {"name": "Peru", "code": "PE"},
            {"name": "Philippines", "code": "PH"},
            {"name": "Pitcairn", "code": "PN"},
            {"name": "Poland", "code": "PL"},
            {"name": "Portugal", "code": "PT"},
            {"name": "Puerto Rico", "code": "PR"},
            {"name": "Qatar", "code": "QA"},
            {"name": "Reunion", "code": "RE"},
            {"name": "Romania", "code": "RO"},
            {"name": "Russian Federation", "code": "RU"},
            {"name": "RWANDA", "code": "RW"},
            {"name": "Saint Helena", "code": "SH"},
            {"name": "Saint Kitts and Nevis", "code": "KN"},
            {"name": "Saint Lucia", "code": "LC"},
            {"name": "Saint Pierre and Miquelon", "code": "PM"},
            {"name": "Saint Vincent and the Grenadines", "code": "VC"},
            {"name": "Samoa", "code": "WS"},
            {"name": "San Marino", "code": "SM"},
            {"name": "Sao Tome and Principe", "code": "ST"},
            {"name": "Saudi Arabia", "code": "SA"},
            {"name": "Senegal", "code": "SN"},
            {"name": "Serbia", "code": "RS"},
            {"name": "Seychelles", "code": "SC"},
            {"name": "Sierra Leone", "code": "SL"},
            {"name": "Singapore", "code": "SG"},
            {"name": "Slovakia", "code": "SK"},
            {"name": "Slovenia", "code": "SI"},
            {"name": "Solomon Islands", "code": "SB"},
            {"name": "Somalia", "code": "SO"},
            {"name": "South Africa", "code": "ZA"},
            {"name": "South Georgia and the South Sandwich Islands", "code": "GS"},
            {"name": "Spain", "code": "ES"},
            {"name": "Sri Lanka", "code": "LK"},
            {"name": "Sudan", "code": "SD"},
            {"name": "Suriname", "code": "SR"},
            {"name": "Svalbard and Jan Mayen", "code": "SJ"},
            {"name": "Swaziland", "code": "SZ"},
            {"name": "Sweden", "code": "SE"},
            {"name": "Switzerland", "code": "CH"},
            {"name": "Syrian Arab Republic", "code": "SY"},
            {"name": "Taiwan, Province of China", "code": "TW"},
            {"name": "Tajikistan", "code": "TJ"},
            {"name": "Tanzania, United Republic of", "code": "TZ"},
            {"name": "Thailand", "code": "TH"},
            {"name": "Timor-Leste", "code": "TL"},
            {"name": "Togo", "code": "TG"},
            {"name": "Tokelau", "code": "TK"},
            {"name": "Tonga", "code": "TO"},
            {"name": "Trinidad and Tobago", "code": "TT"},
            {"name": "Tunisia", "code": "TN"},
            {"name": "Turkey", "code": "TR"},
            {"name": "Turkmenistan", "code": "TM"},
            {"name": "Turks and Caicos Islands", "code": "TC"},
            {"name": "Tuvalu", "code": "TV"},
            {"name": "Uganda", "code": "UG"},
            {"name": "Ukraine", "code": "UA"},
            {"name": "United Arab Emirates", "code": "AE"},
            {"name": "United Kingdom", "code": "GB"},
            {"name": "United States", "code": "US"},
            {"name": "United States Minor Outlying Islands", "code": "UM"},
            {"name": "Uruguay", "code": "UY"},
            {"name": "Uzbekistan", "code": "UZ"},
            {"name": "Vanuatu", "code": "VU"},
            {"name": "Venezuela", "code": "VE"},
            {"name": "Viet Nam", "code": "VN"},
            {"name": "Virgin Islands, British", "code": "VG"},
            {"name": "Virgin Islands, U.S.", "code": "VI"},
            {"name": "Wallis and Futuna", "code": "WF"},
            {"name": "Western Sahara", "code": "EH"},
            {"name": "Yemen", "code": "YE"},
            {"name": "Zambia", "code": "ZM"},
            {"name": "Zimbabwe", "code": "ZW"},
        ]
        return Response(data, status=status.HTTP_200_OK)
    elif request.LANGUAGE_CODE == "ru":
        data = [
            {"code": "au", "name": "Австралия"},
            {"code": "at", "name": "Австрия"},
            {"code": "az", "name": "Азербайджан"},
            {"code": "al", "name": "Албания"},
            {"code": "dz", "name": "Алжир"},
            {"code": "ao", "name": "Ангола"},
            {"code": "ad", "name": "Андорра"},
            {"code": "ag", "name": "Антигуа и Барбуда"},
            {"code": "ar", "name": "Аргентина"},
            {"code": "am", "name": "Армения"},
            {"code": "af", "name": "Афганистан"},
            {"code": "bs", "name": "Багамские Острова"},
            {"code": "bd", "name": "Бангладеш"},
            {"code": "bb", "name": "Барбадос"},
            {"code": "bh", "name": "Бахрейн"},
            {"code": "bz", "name": "Белиз"},
            {"code": "by", "name": "Белоруссия"},
            {"code": "be", "name": "Бельгия"},
            {"code": "bj", "name": "Бенин"},
            {"code": "bg", "name": "Болгария"},
            {"code": "bo", "name": "Боливия"},
            {"code": "ba", "name": "Босния и Герцеговина"},
            {"code": "bw", "name": "Ботсвана"},
            {"code": "br", "name": "Бразилия"},
            {"code": "bn", "name": "Бруней"},
            {"code": "bf", "name": "Буркина-Фасо"},
            {"code": "bi", "name": "Бурунди"},
            {"code": "bt", "name": "Бутан"},
            {"code": "vu", "name": "Вануату"},
            {"code": "gb", "name": "Великобритания"},
            {"code": "hu", "name": "Венгрия"},
            {"code": "ve", "name": "Венесуэла"},
            {"code": "tl", "name": "Восточный Тимор"},
            {"code": "vn", "name": "Вьетнам"},
            {"code": "ga", "name": "Габон"},
            {"code": "ht", "name": "Гаити"},
            {"code": "gy", "name": "Гайана"},
            {"code": "gm", "name": "Гамбия"},
            {"code": "gh", "name": "Гана"},
            {"code": "gt", "name": "Гватемала"},
            {"code": "gn", "name": "Гвинея"},
            {"code": "gw", "name": "Гвинея-Бисау"},
            {"code": "de", "name": "Германия"},
            {"code": "hn", "name": "Гондурас"},
            {"code": "gd", "name": "Гренада"},
            {"code": "gr", "name": "Греция"},
            {"code": "ge", "name": "Грузия"},
            {"code": "dk", "name": "Дания"},
            {"code": "dj", "name": "Джибути"},
            {"code": "dm", "name": "Доминика"},
            {"code": "do", "name": "Доминиканская Республика"},
            {"code": "cd", "name": "ДР Конго"},
            {"code": "eg", "name": "Египет"},
            {"code": "zm", "name": "Замбия"},
            {"code": "zw", "name": "Зимбабве"},
            {"code": "il", "name": "Израиль"},
            {"code": "in", "name": "Индия"},
            {"code": "id", "name": "Индонезия"},
            {"code": "jo", "name": "Иордания"},
            {"code": "iq", "name": "Ирак"},
            {"code": "ir", "name": "Иран"},
            {"code": "ie", "name": "Ирландия"},
            {"code": "is", "name": "Исландия"},
            {"code": "es", "name": "Испания"},
            {"code": "it", "name": "Италия"},
            {"code": "ye", "name": "Йемен"},
            {"code": "cv", "name": "Кабо-Верде"},
            {"code": "kz", "name": "Казахстан"},
            {"code": "kh", "name": "Камбоджа"},
            {"code": "cm", "name": "Камерун"},
            {"code": "ca", "name": "Канада"},
            {"code": "qa", "name": "Катар"},
            {"code": "ke", "name": "Кения"},
            {"code": "cy", "name": "Кипр"},
            {"code": "kg", "name": "Киргизия"},
            {"code": "ki", "name": "Кирибати"},
            {
                "code": "kp",
                "name": "КНДР (Корейская Народно-Демократическая Республика)",
            },
            {"code": "cn", "name": "Китай (Китайская Народная Республика)"},
            {"code": "co", "name": "Колумбия"},
            {"code": "km", "name": "Коморы"},
            {"code": "cr", "name": "Коста-Рика"},
            {"code": "ci", "name": "Кот-д’Ивуар"},
            {"code": "cu", "name": "Куба"},
            {"code": "kw", "name": "Кувейт"},
            {"code": "la", "name": "Лаос"},
            {"code": "lv", "name": "Латвия"},
            {"code": "ls", "name": "Лесото"},
            {"code": "lr", "name": "Либерия"},
            {"code": "lb", "name": "Ливан"},
            {"code": "ly", "name": "Ливия"},
            {"code": "lt", "name": "Литва"},
            {"code": "li", "name": "Лихтенштейн"},
            {"code": "lu", "name": "Люксембург"},
            {"code": "mu", "name": "Маврикий"},
            {"code": "mr", "name": "Мавритания"},
            {"code": "mg", "name": "Мадагаскар"},
            {"code": "mk", "name": "Северная Македония"},
            {"code": "mw", "name": "Малави"},
            {"code": "my", "name": "Малайзия"},
            {"code": "ml", "name": "Мали"},
            {"code": "mv", "name": "Мальдивы"},
            {"code": "mt", "name": "Мальта"},
            {"code": "ma", "name": "Марокко"},
            {"code": "mh", "name": "Маршалловы Острова"},
            {"code": "mx", "name": "Мексика"},
            {"code": "fm", "name": "Микронезия"},
            {"code": "mz", "name": "Мозамбик"},
            {"code": "md", "name": "Молдавия"},
            {"code": "mc", "name": "Монако"},
            {"code": "mn", "name": "Монголия"},
            {"code": "mm", "name": "Мьянма"},
            {"code": "na", "name": "Намибия"},
            {"code": "nr", "name": "Науру"},
            {"code": "np", "name": "Непал"},
            {"code": "ne", "name": "Нигер"},
            {"code": "ng", "name": "Нигерия"},
            {"code": "nl", "name": "Нидерланды"},
            {"code": "ni", "name": "Никарагуа"},
            {"code": "nz", "name": "Новая Зеландия"},
            {"code": "no", "name": "Норвегия"},
            {"code": "ae", "name": "ОАЭ"},
            {"code": "om", "name": "Оман"},
            {"code": "pk", "name": "Пакистан"},
            {"code": "pw", "name": "Палау"},
            {"code": "pa", "name": "Панама"},
            {"code": "pg", "name": "Папуа — Новая Гвинея"},
            {"code": "py", "name": "Парагвай"},
            {"code": "pe", "name": "Перу"},
            {"code": "pl", "name": "Польша"},
            {"code": "pt", "name": "Португалия"},
            {"code": "cg", "name": "Республика Конго"},
            {"code": "kr", "name": "Республика Корея"},
            {"code": "ru", "name": "Россия"},
            {"code": "rw", "name": "Руанда"},
            {"code": "ro", "name": "Румыния"},
            {"code": "sv", "name": "Сальвадор"},
            {"code": "ws", "name": "Самоа"},
            {"code": "sm", "name": "Сан-Марино"},
            {"code": "st", "name": "Сан-Томе и Принсипи"},
            {"code": "sa", "name": "Саудовская Аравия"},
            {"code": "sz", "name": "Эсватини"},
            {"code": "sc", "name": "Сейшельские Острова"},
            {"code": "sn", "name": "Сенегал"},
            {"code": "vc", "name": "Сент-Винсент и Гренадины"},
            {"code": "kn", "name": "Сент-Китс и Невис"},
            {"code": "lc", "name": "Сент-Люсия"},
            {"code": "rs", "name": "Сербия"},
            {"code": "sg", "name": "Сингапур"},
            {"code": "sy", "name": "Сирия"},
            {"code": "sk", "name": "Словакия"},
            {"code": "si", "name": "Словения"},
            {"code": "sb", "name": "Соломоновы Острова"},
            {"code": "so", "name": "Сомали"},
            {"code": "sd", "name": "Судан"},
            {"code": "sr", "name": "Суринам"},
            {"code": "us", "name": "США"},
            {"code": "sl", "name": "Сьерра-Леоне"},
            {"code": "tj", "name": "Таджикистан"},
            {"code": "th", "name": "Таиланд"},
            {"code": "tz", "name": "Танзания"},
            {"code": "tg", "name": "Того"},
            {"code": "to", "name": "Тонга"},
            {"code": "tt", "name": "Тринидад и Тобаго"},
            {"code": "tv", "name": "Тувалу"},
            {"code": "tn", "name": "Тунис"},
            {"code": "tm", "name": "Туркмения"},
            {"code": "tr", "name": "Турция"},
            {"code": "ug", "name": "Уганда"},
            {"code": "uz", "name": "Узбекистан"},
            {"code": "ua", "name": "Украина"},
            {"code": "uy", "name": "Уругвай"},
            {"code": "fj", "name": "Фиджи"},
            {"code": "ph", "name": "Филиппины"},
            {"code": "fi", "name": "Финляндия"},
            {"code": "fr", "name": "Франция"},
            {"code": "hr", "name": "Хорватия"},
            {"code": "cf", "name": "ЦАР"},
            {"code": "td", "name": "Чад"},
            {"code": "me", "name": "Черногория"},
            {"code": "cz", "name": "Чехия"},
            {"code": "cl", "name": "Чили"},
            {"code": "ch", "name": "Швейцария"},
            {"code": "se", "name": "Швеция"},
            {"code": "lk", "name": "Шри-Ланка"},
            {"code": "ec", "name": "Эквадор"},
            {"code": "gq", "name": "Экваториальная Гвинея"},
            {"code": "er", "name": "Эритрея"},
            {"code": "ee", "name": "Эстония"},
            {"code": "et", "name": "Эфиопия"},
            {"code": "za", "name": "ЮАР"},
            {"code": "ss", "name": "Южный Судан"},
            {"code": "jm", "name": "Ямайка"},
            {"code": "jp", "name": "Япония"},
        ]
        return Response(data, status=status.HTTP_200_OK)

    elif request.LANGUAGE_CODE == "uz":
        data = [
            {"code": "AF", "name": "Afgoniston"},
            {"code": "AX", "name": "Aland orollari"},
            {"code": "AL", "name": "Albaniya"},
            {"code": "US", "name": "Amerika Qoshma Shtatlari"},
            {"code": "AS", "name": "Amerika Samoasi"},
            {"code": "AD", "name": "Andorra"},
            {"code": "AI", "name": "Angilya"},
            {"code": "AO", "name": "Angola"},
            {"code": "AQ", "name": "Antarktida"},
            {"code": "AG", "name": "Antigua va Barbuda"},
            {"code": "VI", "name": "AQSH Virgin orollari"},
            {"code": "UM", "name": "AQSH yondosh orollari"},
            {"code": "AR", "name": "Argentina"},
            {"code": "AM", "name": "Armaniston"},
            {"code": "AW", "name": "Aruba"},
            {"code": "AU", "name": "Avstraliya"},
            {"code": "AT", "name": "Avstriya"},
            {"code": "BS", "name": "Bagama orollari"},
            {"code": "BH", "name": "Bahrayn"},
            {"code": "BD", "name": "Bangladesh"},
            {"code": "BB", "name": "Barbados"},
            {"code": "BY", "name": "Belarus"},
            {"code": "BE", "name": "Belgiya"},
            {"code": "BZ", "name": "Beliz"},
            {"code": "BJ", "name": "Benin"},
            {"code": "BM", "name": "Bermuda orollari"},
            {"code": "AE", "name": "Birlashgan Arab Amirliklari"},
            {"code": "BG", "name": "Bolgariya"},
            {"code": "BO", "name": "Boliviya"},
            {"code": "BQ", "name": "Boneyr, Sint-Estatius va Saba"},
            {"code": "BA", "name": "Bosniya va Gertsegovina"},
            {"code": "BW", "name": "Botsvana"},
            {"code": "BR", "name": "Braziliya"},
            {"code": "VG", "name": "Britaniya Virgin orollari"},
            {"code": "IO", "name": "Britaniyaning Hind okeanidagi hududi"},
            {"code": "BN", "name": "Bruney"},
            {"code": "BF", "name": "Burkina-Faso"},
            {"code": "BI", "name": "Burundi"},
            {"code": "BT", "name": "Butan"},
            {"code": "BV", "name": "Buve oroli"},
            {"code": "GB", "name": "Buyuk Britaniya"},
            {"code": "DK", "name": "Daniya"},
            {"code": "DM", "name": "Dominika"},
            {"code": "DO", "name": "Dominikan Respublikasi"},
            {"code": "ET", "name": "Efiopiya"},
            {"code": "EC", "name": "Ekvador"},
            {"code": "GQ", "name": "Ekvatorial Gvineya"},
            {"code": "ER", "name": "Eritreya"},
            {"code": "IR", "name": "Eron"},
            {"code": "EE", "name": "Estoniya"},
            {"code": "PS", "name": "Falastin hududlari"},
            {"code": "FO", "name": "Farer orollari"},
            {"code": "FJ", "name": "Fiji"},
            {"code": "PH", "name": "Filippin"},
            {"code": "FI", "name": "Finlandiya"},
            {"code": "FK", "name": "Folklend orollari"},
            {"code": "FR", "name": "Fransiya"},
            {"code": "GF", "name": "Fransuz Gvianasi"},
            {"code": "TF", "name": "Fransuz Janubiy hududlari"},
            {"code": "PF", "name": "Fransuz Polineziyasi"},
            {"code": "GA", "name": "Gabon"},
            {"code": "HT", "name": "Gaiti"},
            {"code": "GM", "name": "Gambiya"},
            {"code": "GH", "name": "Gana"},
            {"code": "GY", "name": "Gayana"},
            {"code": "DE", "name": "Germaniya"},
            {"code": "GG", "name": "Gernsi"},
            {"code": "GI", "name": "Gibraltar"},
            {"code": "HN", "name": "Gonduras"},
            {"code": "HK", "name": "Gonkong (Xitoy MMH)"},
            {"code": "GD", "name": "Grenada"},
            {"code": "GL", "name": "Grenlandiya"},
            {"code": "GR", "name": "Gretsiya"},
            {"code": "GE", "name": "Gruziya"},
            {"code": "GU", "name": "Guam"},
            {"code": "GP", "name": "Gvadelupe"},
            {"code": "GT", "name": "Gvatemala"},
            {"code": "GN", "name": "Gvineya"},
            {"code": "GW", "name": "Gvineya-Bisau"},
            {"code": "IN", "name": "Hindiston"},
            {"code": "ID", "name": "Indoneziya"},
            {"code": "JO", "name": "Iordaniya"},
            {"code": "IE", "name": "Irlandiya"},
            {"code": "IQ", "name": "Iroq"},
            {"code": "IS", "name": "Islandiya"},
            {"code": "ES", "name": "Ispaniya"},
            {"code": "IL", "name": "Isroil"},
            {"code": "IT", "name": "Italiya"},
            {"code": "ZA", "name": "Janubiy Afrika Respublikasi"},
            {"code": "GS", "name": "Janubiy Georgiya va Janubiy Sendvich orollari"},
            {"code": "KR", "name": "Janubiy Koreya"},
            {"code": "SS", "name": "Janubiy Sudan"},
            {"code": "DZ", "name": "Jazoir"},
            {"code": "JE", "name": "Jersi"},
            {"code": "DJ", "name": "Jibuti"},
            {"code": "CV", "name": "Kabo-Verde"},
            {"code": "KH", "name": "Kambodja"},
            {"code": "CM", "name": "Kamerun"},
            {"code": "CA", "name": "Kanada"},
            {"code": "KY", "name": "Kayman orollari"},
            {"code": "KE", "name": "Keniya"},
            {"code": "CY", "name": "Kipr"},
            {"code": "KI", "name": "Kiribati"},
            {"code": "CC", "name": "Kokos (Kiling) orollari"},
            {"code": "CO", "name": "Kolumbiya"},
            {"code": "KM", "name": "Komor orollari"},
            {"code": "CG", "name": "Kongo Brazzavil"},
            {"code": "CD", "name": "Kongo Kinshasa"},
            {"code": "CR", "name": "Kosta-Rika"},
            {"code": "CI", "name": "Kot-dIvuar"},
            {"code": "CU", "name": "Kuba"},
            {"code": "CK", "name": "Kuk orollari"},
            {"code": "CW", "name": "Kyurasao"},
            {"code": "LA", "name": "Laos"},
            {"code": "LV", "name": "Latviya"},
            {"code": "LS", "name": "Lesoto"},
            {"code": "LR", "name": "Liberiya"},
            {"code": "LT", "name": "Litva"},
            {"code": "LB", "name": "Livan"},
            {"code": "LY", "name": "Liviya"},
            {"code": "LI", "name": "Lixtenshteyn"},
            {"code": "LU", "name": "Lyuksemburg"},
            {"code": "MG", "name": "Madagaskar"},
            {"code": "MO", "name": "Makao (Xitoy MMH)"},
            {"code": "MW", "name": "Malavi"},
            {"code": "MY", "name": "Malayziya"},
            {"code": "MV", "name": "Maldiv orollari"},
            {"code": "ML", "name": "Mali"},
            {"code": "MT", "name": "Malta"},
            {"code": "CF", "name": "Markaziy Afrika Respublikasi"},
            {"code": "MA", "name": "Marokash"},
            {"code": "MQ", "name": "Martinika"},
            {"code": "MH", "name": "Marshall orollari"},
            {"code": "MU", "name": "Mavrikiy"},
            {"code": "MR", "name": "Mavritaniya"},
            {"code": "YT", "name": "Mayotta"},
            {"code": "MX", "name": "Meksika"},
            {"code": "IM", "name": "Men oroli"},
            {"code": "FM", "name": "Mikroneziya"},
            {"code": "EG", "name": "Misr"},
            {"code": "MD", "name": "Moldova"},
            {"code": "MC", "name": "Monako"},
            {"code": "MN", "name": "Mongoliya"},
            {"code": "MS", "name": "Montserrat"},
            {"code": "MZ", "name": "Mozambik"},
            {"code": "SH", "name": "Muqaddas Yelena oroli"},
            {"code": "MM", "name": "Myanma (Birma)"},
            {"code": "NA", "name": "Namibiya"},
            {"code": "NR", "name": "Nauru"},
            {"code": "NP", "name": "Nepal"},
            {"code": "NL", "name": "Niderlandiya"},
            {"code": "NE", "name": "Niger"},
            {"code": "NG", "name": "Nigeriya"},
            {"code": "NI", "name": "Nikaragua"},
            {"code": "NU", "name": "Niue"},
            {"code": "NF", "name": "Norfolk oroli"},
            {"code": "NO", "name": "Norvegiya"},
            {"code": "AZ", "name": "Ozarbayjon"},
            {"code": "PW", "name": "Palau"},
            {"code": "PA", "name": "Panama"},
            {"code": "PG", "name": "Papua Yangi Gvineya"},
            {"code": "PY", "name": "Paragvay"},
            {"code": "PE", "name": "Peru"},
            {"code": "PN", "name": "Pitkern orollari"},
            {"code": "PK", "name": "Pokiston"},
            {"code": "PL", "name": "Polsha"},
            {"code": "PT", "name": "Portugaliya"},
            {"code": "PR", "name": "Puerto-Riko"},
            {"code": "QA", "name": "Qatar"},
            {"code": "KG", "name": "Qirgiziston"},
            {"code": "KZ", "name": "Qozogiston"},
            {"code": "KW", "name": "Quvayt"},
            {"code": "RE", "name": "Reyunion"},
            {"code": "CX", "name": "Rojdestvo oroli"},
            {"code": "RU", "name": "Rossiya"},
            {"code": "RW", "name": "Ruanda"},
            {"code": "RO", "name": "Ruminiya"},
            {"code": "SV", "name": "Salvador"},
            {"code": "WS", "name": "Samoa"},
            {"code": "SM", "name": "San-Marino"},
            {"code": "ST", "name": "San-Tome va Prinsipi"},
            {"code": "SA", "name": "Saudiya Arabistoni"},
            {"code": "BL", "name": "Sen-Bartelemi"},
            {"code": "PM", "name": "Sen-Pyer va Mikelon"},
            {"code": "SN", "name": "Senegal"},
            {"code": "KN", "name": "Sent-Kits va Nevis"},
            {"code": "LC", "name": "Sent-Lyusiya"},
            {"code": "MF", "name": "Sent-Martin"},
            {"code": "VC", "name": "Sent-Vinsent va Grenadin"},
            {"code": "RS", "name": "Serbiya"},
            {"code": "SC", "name": "Seyshel orollari"},
            {"code": "SG", "name": "Singapur"},
            {"code": "SX", "name": "Sint-Marten"},
            {"code": "SK", "name": "Slovakiya"},
            {"code": "SI", "name": "Sloveniya"},
            {"code": "SB", "name": "Solomon orollari"},
            {"code": "SO", "name": "Somali"},
            {"code": "SD", "name": "Sudan"},
            {"code": "SR", "name": "Surinam"},
            {"code": "SY", "name": "Suriya"},
            {"code": "SZ", "name": "Svazilend"},
            {"code": "SL", "name": "Syerra-Leone"},
            {"code": "TH", "name": "Tailand"},
            {"code": "TZ", "name": "Tanzaniya"},
            {"code": "TW", "name": "Tayvan"},
            {"code": "TL", "name": "Timor-Leste"},
            {"code": "TG", "name": "Togo"},
            {"code": "TJ", "name": "Tojikiston"},
            {"code": "TK", "name": "Tokelau"},
            {"code": "TO", "name": "Tonga"},
            {"code": "TT", "name": "Trinidad va Tobago"},
            {"code": "TN", "name": "Tunis"},
            {"code": "TR", "name": "Turkiya"},
            {"code": "TM", "name": "Turkmaniston"},
            {"code": "TC", "name": "Turks va Kaykos orollari"},
            {"code": "TV", "name": "Tuvalu"},
            {"code": "UG", "name": "Uganda"},
            {"code": "UA", "name": "Ukraina"},
            {"code": "OM", "name": "Ummon"},
            {"code": "WF", "name": "Uollis va Futuna"},
            {"code": "UY", "name": "Urugvay"},
            {"code": "VU", "name": "Vanuatu"},
            {"code": "VA", "name": "Vatikan"},
            {"code": "VE", "name": "Venesuela"},
            {"code": "HU", "name": "Vengriya"},
            {"code": "VN", "name": "Vyetnam"},
            {"code": "HM", "name": "Xerd va Makdonald orollari"},
            {"code": "CN", "name": "Xitoy"},
            {"code": "HR", "name": "Xorvatiya"},
            {"code": "YE", "name": "Yaman"},
            {"code": "JM", "name": "Yamayka"},
            {"code": "NC", "name": "Yangi Kaledoniya"},
            {"code": "NZ", "name": "Yangi Zelandiya"},
            {"code": "JP", "name": "Yaponiya"},
            {"code": "ZM", "name": "Zambiya"},
            {"code": "ZW", "name": "Zimbabve"},
            {"code": "UZ", "name": "Ozbekiston"},
            {"code": "EH", "name": "Garbiy Sahroi Kabir"},
            {"code": "KP", "name": "Shimoliy Koreya"},
            {"code": "MK", "name": "Shimoliy Makedoniya"},
            {"code": "MP", "name": "Shimoliy Mariana orollari"},
            {"code": "SJ", "name": "Shpitsbergen va Yan-Mayen"},
            {"code": "LK", "name": "Shri-Lanka"},
            {"code": "SE", "name": "Shvetsiya"},
            {"code": "CH", "name": "Shveytsariya"},
            {"code": "TD", "name": "Chad"},
            {"code": "ME", "name": "Chernogoriya"},
            {"code": "CZ", "name": "Chexiya"},
            {"code": "CL", "name": "Chili"},
        ]
        return Response(data, status=status.HTTP_200_OK)
    else:
        return Response(
            "Please provide locale prefix (uz/ru/en)",
            status=status.HTTP_400_BAD_REQUEST,
        )
