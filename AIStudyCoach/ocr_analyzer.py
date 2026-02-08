import pytesseract
from PIL import Image, ImageFilter, ImageOps
import re
import json
import os
from translator import TranslationManager

class PrescriptionAnalyzer:
    def __init__(self):
        self.translator = TranslationManager()
        self.last_error = None
        # Auto-configure Tesseract on Windows if not on PATH
        try:
            if os.name == "nt":
                configured = False
                # 1) Respect explicit env override if provided
                env_path = os.environ.get("TESSERACT_PATH")
                if env_path and os.path.exists(env_path):
                    pytesseract.pytesseract.tesseract_cmd = env_path
                    configured = True
                # 2) Fall back to common default install location
                default_path = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
                if not configured and os.path.exists(default_path):
                    pytesseract.pytesseract.tesseract_cmd = default_path
                    configured = True
                # No exception if not found; UI will surface guidance
        except Exception:
            # Silently ignore auto-config failures; runtime checks will report
            pass
        
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
        
        # Dosage forms and stopwords to reduce false positives
        self.form_keywords = [
            'tab', 'tabs', 'tablet', 'tablets',
            'cap', 'caps', 'capsule', 'capsules',
            'syrup', 'drops', 'drop', 'ointment', 'cream', 'gel'
        ]
        self.stopwords = set([
            'prescription','rx','sig','follow','stare','note','date','name','age','sex','m','f','address','doctor','physician',
            'dose','dosage','advice','morning','evening','night','daily','day','days'
        ])
        
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
    
    def _preprocess(self, image: Image.Image) -> list[Image.Image]:
        """Generate a set of enhanced variants to improve OCR robustness."""
        variants = []
        # Always include upscaled versions (helps printed forms)
        try:
            up1 = image.resize((int(image.width*1.5), int(image.height*1.5)))
            up2 = image.resize((image.width*2, image.height*2))
            variants.extend([up1, up2])
        except Exception:
            pass
        try:
            import cv2
            import numpy as np
            # Convert PIL -> OpenCV
            img_cv = cv2.cvtColor(np.array(image.convert('RGB')), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            # Denoise and threshold variants
            blur = cv2.medianBlur(gray, 3)
            _, th_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            th_adapt = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11)
            # Sharpen a bit
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
            sharp = cv2.filter2D(gray, -1, kernel)
            # Back to PIL
            for arr in [gray, blur, th_otsu, th_adapt, sharp]:
                variants.append(Image.fromarray(arr))
        except Exception:
            # Fallback: Pillow-only variants
            g = ImageOps.grayscale(image)
            variants.extend([
                g,
                ImageOps.autocontrast(g.filter(ImageFilter.MedianFilter(size=3))),
                ImageOps.invert(ImageOps.autocontrast(g)),
            ])
        # Also include original
        variants.insert(0, image)
        return variants

    def analyze_prescription(self, image, target_language='en', tesseract_lang='eng'):
        """Analyze prescription image using OCR"""
        try:
            # Ensure Tesseract is available
            self.last_error = None
            try:
                _ = pytesseract.get_tesseract_version()
            except Exception as te:
                self.last_error = f"Tesseract OCR not available: {te}"
                return None
            # Try multiple preprocessing variants and PSM configs
            variants = self._preprocess(image)
            configs = [
                "--oem 3 --psm 6 -c preserve_interword_spaces=1",
                "--oem 3 --psm 4 -c preserve_interword_spaces=1",
                "--oem 1 --psm 7",
                "--oem 3 --psm 11",  # sparse text
                "--oem 3 --psm 12",  # sparse text with OSD
            ]
            extracted_text = ""
            for variant in variants:
                for cfg in configs:
                    try:
                        text_try = pytesseract.image_to_string(variant, lang=tesseract_lang, config=cfg)
                        if len(text_try.strip()) > len(extracted_text.strip()):
                            extracted_text = text_try
                    except Exception:
                        continue
            
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
        
        row_regex = re.compile(r"^\s*(?:\d+[\).]\s*)?(?:TAB\.?|CAP\.?|SYRUP|DROPS|OINT\.?|CREAM|GEL)?\s*([A-Za-z][A-Za-z0-9_-]{3,})(?:\s+(\d+\s*(?:mg|mcg|g|ml|iu)))?", re.IGNORECASE)

        # Try to focus on the prescription table between known headers
        in_table = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Drop obvious non-medicine headers in printed prescriptions
            tokens = set(line.lower().split())
            if tokens & {"chief","diagnosis","advice","after","weight","closed","medicine","medicines"}:
                continue
            low = line.lower()
            if any(h in low for h in ["medicine name", "medicine", "medicines"]):
                in_table = True
                continue
            if any(h in low for h in ["advice", "follow up", "follow-up", "followup"]):
                in_table = False
            
            
            # Prefer extracting around strengths/forms
            medication_name = self.extract_medication_candidate(line)
            if not medication_name:
                # Fallback to dictionary/heuristic
                medication_name = self.extract_medication_name(line)
            # Printed-table style match
            if not medication_name:
                mrow = row_regex.match(line)
                if mrow:
                    medication_name = mrow.group(1).title()
                    guessed_dose = mrow.group(2)
                else:
                    guessed_dose = None
            # If inside table, try simple column split heuristic
            if not medication_name and in_table:
                # Lines often look like: "1) TAB. ACBCIXIMAB          1 Morning          8 Days"
                parts = re.split(r"\s{2,}", line)
                if len(parts) >= 1:
                    # Strip leading numbering and dosage form markers
                    first = re.sub(r"^\d+[).]\s*", "", parts[0])
                    first = re.sub(r"\b(?:tab\.?|caps?\.?|syrup|drops|ointment|cream|gel)\b\.?", "", first, flags=re.IGNORECASE).strip()
                    # Ignore obvious non-medicine words
                    if first and first.lower() not in self.stopwords and len(first) > 3:
                        medication_name = first.title()
                if not guessed_dose and len(parts) >= 2:
                    guessed_dose = self.extract_dosage(parts[0]) or self.extract_dosage(parts[1])
            if medication_name:
                medication = {
                    'name': medication_name,
                    'dosage': self.extract_dosage(line) or (guessed_dose if 'guessed_dose' in locals() else None),
                    'frequency': self.extract_frequency(line),
                    'duration': self.extract_duration(line),
                    'instructions': self.extract_instructions(line),
                    'info': self.medication_info.get(medication_name, 'Medication information not available')
                }
                medications.append(medication)
        
        # Global pass: also look for Name + Strength patterns across full text when line parsing is weak
        joined = " \n".join([ln for ln in lines if ln.strip()])
        for m in re.finditer(r"([A-Za-z][A-Za-z0-9-]{3,})\s+(\d+\s*(?:mg|mcg|g|ml|iu))", joined, flags=re.IGNORECASE):
            name = m.group(1).title()
            if name.lower() in self.stopwords:
                continue
            if not any(mi['name'].lower() == name.lower() for mi in medications):
                medications.append({
                    'name': name,
                    'dosage': m.group(2),
                    'frequency': None,
                    'duration': None,
                    'instructions': None,
                    'info': self.medication_info.get(name.lower(), 'Medication information not available')
                })

        # Final filtering: keep items that have a plausible name and at least one detail
        filtered: list[dict] = []
        for med in medications:
            name_ok = med.get('name') and med['name'].strip() and med['name'].lower() not in self.stopwords
            # Relax: allow items with only name or only dosage
            has_any = any([med.get('dosage'), med.get('frequency'), med.get('duration')])
            if name_ok and (has_any or len(med['name']) >= 5):
                filtered.append(med)
        return filtered

    def extract_medication_candidate(self, text: str):
        """Try to extract a medication name using units/forms context and filter stopwords."""
        text_low = text.lower()
        # Skip lines that are obviously non-med lines
        if any(sw in text_low.split() for sw in self.stopwords):
            pass  # do not early return; might still contain a valid line
        # Strength/units
        unit_match = re.search(r'(\d+\s*(?:mg|mcg|g|ml|iu))', text_low)
        form_present = any(f in text_low for f in self.form_keywords)
        if unit_match or form_present:
            # Take up to three tokens before the first unit/form keyword as candidate name
            tokens = re.split(r'[^a-zA-Z0-9+-]+', text)
            # find index of token containing unit/form
            idx = None
            for i, tok in enumerate(tokens):
                if re.search(r'(?:mg|mcg|g|ml|iu)$', tok.lower()) or tok.lower() in self.form_keywords:
                    idx = i
                    break
            if idx is None and unit_match:
                # find index of token where the numeric part appears
                num = unit_match.group(1).split()[0]
                for i, tok in enumerate(tokens):
                    if num in tok:
                        idx = i
                        break
            # Build candidate from up to three previous tokens
            if idx is not None:
                start = max(0, idx-3)
                candidate_tokens = [t for t in tokens[start:idx] if t and t.isalpha()]
                if candidate_tokens:
                    cand = candidate_tokens[-1]
                    cand_low = cand.lower()
                    if cand_low not in self.stopwords and len(cand) > 3:
                        return cand.title()
        return None
    
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
