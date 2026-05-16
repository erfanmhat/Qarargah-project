#!/usr/bin/env python3
"""
اسکریپت اسکن ساختار پروژه قرارگاه
خروجی: لیست فایل‌های پایتون، تمپلیت‌ها، و تنظیمات
"""
import os
from pathlib import Path
from collections import defaultdict

def scan_project_structure(root_path="."):
    """اسکن پوشه‌های پروژه و دسته‌بندی فایل‌ها"""
    
    structure = {
        "python_files": [],
        "templates": [],
        "static_files": [],
        "config_files": [],
        "migrations": []
    }
    
    # پوشه‌هایی که نباید اسکن شوند
    exclude_dirs = {
        '__pycache__', '.git', 'venv', 'env', 
        '.venv', 'node_modules', 'staticfiles', 'media'
    }
    
    root = Path(root_path)
    
    for item in root.rglob('*'):
        # رد کردن پوشه‌های exclude
        if any(ex in item.parts for ex in exclude_dirs):
            continue
            
        if item.is_file():
            rel_path = item.relative_to(root)
            
            # فایل‌های پایتون
            if item.suffix == '.py':
                if 'migrations' in item.parts:
                    structure["migrations"].append(str(rel_path))
                else:
                    structure["python_files"].append(str(rel_path))
            
            # تمپلیت‌ها
            elif item.suffix == '.html':
                structure["templates"].append(str(rel_path))
            
            # فایل‌های استاتیک
            elif item.suffix in {'.css', '.js', '.json'}:
                structure["static_files"].append(str(rel_path))
            
            # فایل‌های تنظیمات
            elif item.name in {'settings.py', 'urls.py', 'wsgi.py', 
                              'asgi.py', 'requirements.txt', '.env', 
                              'manage.py', 'TODO_QARARGAH.md'}:
                structure["config_files"].append(str(rel_path))
    
    return structure


def print_structure(structure):
    """چاپ ساختار به صورت خوانا"""
    
    print("=" * 60)
    print("ساختار پروژه قرارگاه (اپ core)")
    print("=" * 60)
    
    # فایل‌های پایتون به تفکیک اپ
    print("\n📦 فایل‌های پایتون (به تفکیک ماژول):")
    print("-" * 60)
    
    apps = defaultdict(list)
    for f in sorted(structure["python_files"]):
        parts = Path(f).parts
        if len(parts) > 1 and parts[0] == 'core':
            app_name = parts[1] if len(parts) > 1 else 'root'
            apps[app_name].append(f)
        else:
            apps['root'].append(f)
    
    for app, files in sorted(apps.items()):
        print(f"\n  [{app}]")
        for f in files:
            print(f"    • {f}")
    
    # تمپلیت‌ها
    if structure["templates"]:
        print("\n\n🎨 تمپلیت‌های HTML:")
        print("-" * 60)
        for f in sorted(structure["templates"]):
            print(f"  • {f}")
    
    # فایل‌های تنظیمات
    if structure["config_files"]:
        print("\n\n⚙️  فایل‌های تنظیمات:")
        print("-" * 60)
        for f in sorted(structure["config_files"]):
            print(f"  • {f}")
    
    # migrations
    if structure["migrations"]:
        print("\n\n🔄 Migrations:")
        print("-" * 60)
        migration_apps = defaultdict(list)
        for f in sorted(structure["migrations"]):
            parts = Path(f).parts
            if 'migrations' in parts:
                idx = parts.index('migrations')
                if idx > 0:
                    app = parts[idx - 1]
                    migration_apps[app].append(Path(f).name)
        
        for app, migs in sorted(migration_apps.items()):
            print(f"\n  [{app}]")
            for m in migs:
                if m != '__init__.py':
                    print(f"    • {m}")
    
    # آمار کلی
    print("\n\n📊 آمار:")
    print("-" * 60)
    print(f"  فایل‌های پایتون: {len(structure['python_files'])}")
    print(f"  تمپلیت‌ها: {len(structure['templates'])}")
    print(f"  فایل‌های استاتیک: {len(structure['static_files'])}")
    print(f"  Migrations: {len(structure['migrations'])}")
    print("=" * 60)


if __name__ == "__main__":
    structure = scan_project_structure()
    print_structure(structure)