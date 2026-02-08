from googletrans import Translator
import os

class TranslationManager:
    def __init__(self):
        self.translator = Translator()
        
        # Language mappings
        self.languages = {
            'en': 'English',
            'hi': 'Hindi',
            'bn': 'Bengali', 
            'or': 'Odia',
            'ml': 'Malayalam'
        }
        
        # Cache for translations to avoid repeated API calls
        self.translation_cache = {}
    
    def translate_text(self, text, target_language='en'):
        """Translate text to target language"""
        if not text or not text.strip():
            return text
        
        # Don't translate if already in English and target is English
        if target_language == 'en':
            return text
        
        # Check cache first
        cache_key = f"{text}_{target_language}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        try:
            # Perform translation
            result = self.translator.translate(text, dest=target_language)
            translated_text = result.text
            
            # Cache the result
            self.translation_cache[cache_key] = translated_text
            
            return translated_text
        
        except Exception as e:
            print(f"Translation Error: {str(e)}")
            # Return original text if translation fails
            return text
    
    def detect_language(self, text):
        """Detect the language of given text"""
        try:
            detection = self.translator.detect(text)
            return detection.lang
        except Exception as e:
            print(f"Language Detection Error: {str(e)}")
            return 'en'  # Default to English
    
    def get_supported_languages(self):
        """Get list of supported languages"""
        return self.languages
    
    def batch_translate(self, texts, target_language='en'):
        """Translate multiple texts at once"""
        translated_texts = []
        
        for text in texts:
            translated_text = self.translate_text(text, target_language)
            translated_texts.append(translated_text)
        
        return translated_texts
    
    def translate_medical_terms(self, terms, target_language='en'):
        """Translate medical terms with special handling"""
        medical_translations = {}
        
        # Common medical terms that should be handled carefully
        medical_glossary = {
            'prescription': {
                'hi': 'नुस्खा',
                'bn': 'প্রেসক্রিপশন',
                'or': 'ପ୍ରେସକ୍ରିପସନ୍',
                'ml': 'കുറിപ്പടി'
            },
            'medicine': {
                'hi': 'दवा',
                'bn': 'ওষুধ',
                'or': 'ଔଷଧ',
                'ml': 'മരുന്ന്'
            },
            'dosage': {
                'hi': 'खुराक',
                'bn': 'ডোজ',
                'or': 'ମାତ୍ରା',
                'ml': 'അളവ്'
            },
            'doctor': {
                'hi': 'डॉक्टर',
                'bn': 'ডাক্তার',
                'or': 'ଡାକ୍ତର',
                'ml': 'ഡോക്ടർ'
            },
            'hospital': {
                'hi': 'अस्पताल',
                'bn': 'হাসপাতাল',
                'or': 'ଡାକ୍ତରଖାନା',
                'ml': 'ആശുപത്രി'
            }
        }
        
        for term in terms:
            term_lower = term.lower()
            if term_lower in medical_glossary and target_language in medical_glossary[term_lower]:
                medical_translations[term] = medical_glossary[term_lower][target_language]
            else:
                medical_translations[term] = self.translate_text(term, target_language)
        
        return medical_translations
