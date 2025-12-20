## Create and compile messages for translations

All translation files are located in locale directory. To create and compile messages for translations, run the following commands:

- Create or update .po files for all languages by also ignoring unnecessary files (--i option)

```bash
django-admin makemessages -a --i "migrations/*" --i "venv/*" --i ".git/*"  --i "tests/*"  --i "node_modules/*"  --i "static/*"  --i "media/*"  --i "__pycache__/*"

# for a specific language
python manage.py makemessages -l uz --i "migrations/*" --i "venv/*" --i ".git/*"  --i "tests/*"  --i "node_modules/*"  --i "static/*"  --i "media/*"  --i "__pycache__/*"
```

Change ignore options as needed.

### Compiling Messages (create .mo files)

```bash
python manage.py compilemessages
# for a specific language
python manage.py compilemessages -l ru
```
