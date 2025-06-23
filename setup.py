from setuptools import setup, find_packages

setup(
    name="project_modules",  # это имя будет использоваться в импортах
    version="0.1.0",
    packages=find_packages(include=["project_modules", "project_modules.*"]),
    install_requires=[
        "requests",
        "psycopg2",
        "beautifulsoup4",
        "lxml",
        "selenium",
        "tabulate"
    ],
    description="Общие модули и утилиты",
    author="Kutipotai",
    author_email="Kutipotai@google.com",
    include_package_data=True,
    zip_safe=False,
)

'''
✅ Установка из Git
После того как ты зальёшь project_libs/ на GitHub, добавь в requirements.txt другого проекта:
git+https://github.com/yourusername/project_libs.git@main#egg=project_modules

✅ Проверка локально (без Git)
pip install -e /path/to/project_libs

'''