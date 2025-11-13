# debug_pdf.py
import os
import sys
import django

# Configuration Django
sys.path.append('/home/pi/intranet_international')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'votre_projet.settings')
django.setup()

from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
import requests
from io import BytesIO
import mimetypes
from urllib.parse import urlparse
from pathlib import Path
from django.conf import settings
from django.contrib.staticfiles import finders
import weasyprint

def debug_url_fetcher(url, *args, **kwargs):
    """URL fetcher avec logging détaillé"""
    print(f"🔍 [URL_FETCHER] Tentative de récupération: {url}")
    
    # Test DNS
    if url.startswith(('http://', 'https://')):
        try:
            parsed = urlparse(url)
            print(f"   🌐 Domain: {parsed.netloc}, Path: {parsed.path}")
            
            # Test de connexion basique
            response = requests.get(url, timeout=5, verify=False)
            print(f"   ✅ HTTP Status: {response.status_code}")
            print(f"   📦 Content-Type: {response.headers.get('content-type')}")
            print(f"   📏 Content-Length: {len(response.content)} bytes")
            
            return {
                'file_obj': BytesIO(response.content),
                'mime_type': response.headers.get('content-type'),
                'encoding': response.encoding,
            }
        except Exception as e:
            print(f"   ❌ ERREUR HTTP: {e}")
    
    # Fallback vers le fetcher par défaut
    try:
        result = weasyprint.default_url_fetcher(url, *args, **kwargs)
        print(f"   ✅ Default fetcher a réussi")
        return result
    except Exception as e:
        print(f"   ❌ Default fetcher a échoué: {e}")
        # Retourner un fichier vide
        return {
            'file_obj': BytesIO(b''),
            'mime_type': 'application/octet-stream',
            'encoding': None,
        }

def test_pdf_generation():
    """Test de génération PDF avec un utilisateur spécifique"""
    from users.models import CustomUser
    
    try:
        # Récupérer un utilisateur de test
        user = CustomUser.objects.first()
        print(f"👤 Utilisateur de test: {user}")
        
        # Générer le HTML
        context = {
            'employee': user,
            'year': 2024,
            'generation_date': '15 Décembre 2024'
        }
        
        html_string = render_to_string('rh/attestation_pdf.html', context)
        print("✅ HTML généré avec succès")
        
        # Tester avec le fetcher de debug
        print("\n🚀 TEST AVEC DEBUG FETCHER:")
        html = HTML(
            string=html_string, 
            base_url='http://localhost:8000/',
            url_fetcher=debug_url_fetcher
        )
        
        pdf = html.write_pdf()
        print(f"✅ PDF généré: {len(pdf)} bytes")
        
        # Sauvegarder pour inspection
        with open('/tmp/debug_test.pdf', 'wb') as f:
            f.write(pdf)
        print("💾 PDF sauvegardé dans /tmp/debug_test.pdf")
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_generation()