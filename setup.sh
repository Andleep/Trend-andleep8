#!/bin/bash
echo "🚀 بدء تثبيت المتطلبات..."
python -m pip install --upgrade pip
pip install wheel setuptools
pip install -r requirements.txt
echo "✅ تم التثبيت بنجاح!"
