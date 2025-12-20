from django.shortcuts import render


def notification_view(request, username):
    return render(request, 'notification/index.html', {"username": username})