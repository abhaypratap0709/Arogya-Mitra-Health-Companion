import pytesseract
from PIL import Image
import re
import json
from translator import TranslationManager

class PrescriptionAnalyzer:
    def __init__(self):
        self.translator = TranslationManager()
        self.last_error = None
        
        # Common medication patterns
        self.dosage_patterns = [
            r'(\d+)\s*mg',
            r'(\d+)\s*ml',
            r'(\d+)\s*tablet[s]?',
            r'(\d+)\s*capsule[s]?',
            r'(\d+-\d+-\d+)',  # Dosage format like 1-0-1
        ]
        
        self.frequency_patterns = [
            r'once\s+daily',
            r'twice\s+daily',
            r'thrice\s+daily',
            r'\d+\s+times?\s+(?:a\s+)?day',
            r'before\s+meals?',
            r'after\s+meals?',
            r'with\s+meals?',
            r'empty\s+stomach',
            r'at\s+bedtime',
            r'morning',
            r'evening',
        ]
        
        self.duration_patterns = [
            r'for\s+(\d+)\s+days?',
            r'for\s+(\d+)\s+weeks?',
            r'for\s+(\d+)\s+months?',
            r'continue\s+for\s+(\d+)',
        ]
        
        # Common medication database (simplified)
        self.medication_info = {
            'paracetamol': 'Pain relief and fever reducer',
            'acetaminophen': 'Pain relief and fever reducer',
            'ibuprofen': 'Anti-inflammatory and pain relief',
            'aspirin': 'Pain relief and blood thinner',
            'amoxicillin': 'Antibiotic for bacterial infections',
            'azithromycin': 'Antibiotic for bacterial infections',
            'metformin': 'Diabetes medication',
            'omeprazole': 'Acid reflux and stomach acid reducer',
            'cetirizine': 'Antihistamine for allergies',
            'loratadine': 'Antihistamine for allergies',
            'cough syrup': 'Relief from cough symptoms',
            'vitamin d': 'Vitamin supplement for bone health',
            'calcium': 'Mineral supplement for bone health',
            'iron': 'Supplement for anemia',
        }
    
    def analyze_prescription(self, image, target_language='en'):
        """Analyze prescription image using OCR"""
        try:
            # Ensure Tesseract is available
            self.last_error = None
            try:
                _ = pytesseract.get_tesseract_version()
            except Exception as te:
                self.last_error = f"Tesseract OCR not available: {te}"
                return None
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(image, lang='eng')
            
            if not extracted_text.strip():
                return None
            
            # Parse medications from text
            medications = self.parse_medications(extracted_text.lower())
            
            # Translate if needed
            if target_language != 'en':
                extracted_text = self.translator.translate_text(extracted_text, target_language)
                for med in medications:
                    if med['instructions']:
                        med['instructions'] = self.translator.translate_text(med['instructions'], target_language)
            
            return {
                'extracted_text': extracted_text,
                'medications': medications
            }
        
        except Exception as e:
            print(f"OCR Analysis Error: {str(e)}")
            return None

    def is_tesseract_available(self):
        """Check if local Tesseract binary is available"""
        try:
            _ = pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            self.last_error = str(e)
            return False
    
    def parse_medications(self, text):
        """Parse medications and their details from extracted text"""
        medications = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line contains medication name
            medication_name = self.extract_medication_name(line)
            if medication_name:
                medication = {
                    'name': medication_name,
                    'dosage': self.extract_dosage(line),
                    'frequency': self.extract_frequency(line),
                    'duration': self.extract_duration(line),
                    'instructions': self.extract_instructions(line),
                    'info': self.medication_info.get(medication_name, 'Medication information not available')
                }
                medications.append(medication)
        
        return medications
    
    def extract_medication_name(self, text):
        """Extract medication name from text"""
        # Look for known medications
        for med_name in self.medication_info.keys():
            if med_name in text.lower():
                return med_name.title()
        
        # Try to extract potential medication names (usually at the beginning of line)
        words = text.split()
        if words:
            # If first word looks like a medication name (contains letters and possibly numbers)
            first_word = words[0].strip('.,()[]')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', first_word) and len(first_word) > 3:
                return first_word.title()
        
        return None
    
    def extract_dosage(self, text):
        """Extract dosage information"""
        for pattern in self.dosage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def extract_frequency(self, text):
        """Extract frequency information"""
        for pattern in self.frequency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def extract_duration(self, text):
        """Extract duration information"""
        for pattern in self.duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def extract_instructions(self, text):
        """Extract additional instructions"""
        instruction_keywords = [
            'before meals', 'after meals', 'with meals', 'empty stomach',
            'with water', 'do not crush', 'take with food', 'avoid alcohol'
        ]
        
        found_instructions = []
        for keyword in instruction_keywords:
            if keyword in text.lower():
                found_instructions.append(keyword)
        
        return ', '.join(found_instructions) if found_instructions else None
    
    def get_medication_warnings(self, medication_name):
        """Get warnings for specific medications"""
        warnings = {
            'paracetamol': 'Do not exceed 4g per day. Avoid alcohol.',
            'ibuprofen': 'Take with food. May cause stomach irritation.',
            'aspirin': 'May cause bleeding. Consult doctor if on blood thinners.',
            'antibiotics': 'Complete the full course even if feeling better.',
        }
        
        # Check if medication matches any warning category
        medication_lower = medication_name.lower()
        for key, warning in warnings.items():
            if key in medication_lower:
                return warning
        
        return None
