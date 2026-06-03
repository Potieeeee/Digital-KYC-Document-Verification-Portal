#!/usr/bin/env bash

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py create_roles

DEFAULT_REVIEWER_USERNAME=${DEFAULT_REVIEWER_USERNAME:-reviewer}
DEFAULT_REVIEWER_EMAIL=${DEFAULT_REVIEWER_EMAIL:-reviewer@example.com}
DEFAULT_REVIEWER_PASSWORD=${DEFAULT_REVIEWER_PASSWORD:-reviewerpassword}

python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()
username = os.getenv('DEFAULT_REVIEWER_USERNAME', 'reviewer')
email = os.getenv('DEFAULT_REVIEWER_EMAIL', 'reviewer@example.com')
password = os.getenv('DEFAULT_REVIEWER_PASSWORD', 'reviewerpassword')

if User.objects.filter(username=username).exists():
    print(f'Default reviewer already exists: {username}')
else:
    user = User.objects.create_user(username=username, email=email, password=password)
    reviewer_group, _ = Group.objects.get_or_create(name='Reviewer')
    user.groups.add(reviewer_group)
    user.save()
    print(f'Default reviewer created: {username}')
PY