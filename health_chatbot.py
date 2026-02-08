import streamlit as st
import re
from datetime import datetime
from translator import TranslationManager

class HealthChatbot:
    def __init__(self):
        self.translator = TranslationManager()
        
        # Health knowledge base with keywords and responses
        self.health_knowledge = {
            # Fever related
            'fever': {
                'keywords': ['fever', 'temperature', 'hot', 'burning', 'pyrexia', 'high temp'],
                'response': {
                    'en': """🌡️ **Fever Information:**
                    
**Symptoms:** High body temperature (>100.4°F/38°C), chills, sweating, headache, muscle aches

**Immediate Care:**
• Rest and stay hydrated
• Take paracetamol (500-1000mg every 6 hours)
• Use cool compresses
• Monitor temperature regularly

**When to see a doctor:**
• Fever >103°F (39.4°C)
• Fever lasting >3 days
• Severe headache or neck stiffness
• Difficulty breathing
• Rash with fever

**⚠️ Emergency:** If fever is very high (>104°F) or accompanied by severe symptoms, seek immediate medical attention.""",
                    'hi': """🌡️ **बुखार की जानकारी:**
                    
**लक्षण:** उच्च शरीर का तापमान (>100.4°F/38°C), ठंड लगना, पसीना, सिरदर्द, मांसपेशियों में दर्द

**तुरंत देखभाल:**
• आराम करें और हाइड्रेटेड रहें
• पैरासिटामोल लें (500-1000mg हर 6 घंटे)
• ठंडे कपड़े का उपयोग करें
• तापमान की नियमित निगरानी करें

**डॉक्टर से कब मिलें:**
• बुखार >103°F (39.4°C)
• बुखार 3 दिन से अधिक
• गंभीर सिरदर्द या गर्दन में अकड़न
• सांस लेने में कठिनाई
• बुखार के साथ चकत्ते

**⚠️ आपातकाल:** यदि बुखार बहुत अधिक (>104°F) है या गंभीर लक्षणों के साथ है, तो तुरंत चिकित्सा सहायता लें।"""
                }
            },
            
            # Cold related
            'cold': {
                'keywords': ['cold', 'common cold', 'runny nose', 'nasal congestion', 'sneezing', 'stuffy nose'],
                'response': {
                    'en': """🤧 **Common Cold Information:**
                    
**Symptoms:** Runny nose, sneezing, sore throat, mild cough, congestion

**Home Remedies:**
• Drink warm fluids (tea, soup)
• Use saline nasal drops
• Gargle with warm salt water
• Get plenty of rest
• Use humidifier

**Medications:**
• Paracetamol for fever/pain
• Antihistamines for runny nose
• Decongestants for stuffy nose
• Throat lozenges for sore throat

**Duration:** Usually resolves in 7-10 days

**When to see a doctor:**
• Symptoms worsen after 5 days
• High fever (>101°F)
• Severe headache or sinus pain
• Difficulty breathing""",
                    'hi': """🤧 **सामान्य सर्दी की जानकारी:**
                    
**लक्षण:** बहती नाक, छींकना, गले में खराश, हल्की खांसी, भीड़

**घरेलू उपचार:**
• गर्म तरल पदार्थ पिएं (चाय, सूप)
• नमकीन नाक की बूंदें उपयोग करें
• गर्म नमक के पानी से गरारे करें
• भरपूर आराम करें
• ह्यूमिडिफायर का उपयोग करें

**दवाएं:**
• बुखार/दर्द के लिए पैरासिटामोल
• बहती नाक के लिए एंटीहिस्टामाइन
• भीड़ के लिए डिकॉन्गेस्टेंट
• गले में खराश के लिए गले की गोलियां

**अवधि:** आमतौर पर 7-10 दिनों में ठीक हो जाता है

**डॉक्टर से कब मिलें:**
• 5 दिन बाद लक्षण बिगड़ते हैं
• उच्च बुखार (>101°F)
• गंभीर सिरदर्द या साइनस दर्द
• सांस लेने में कठिनाई"""
                }
            },
            
            # Cough related
            'cough': {
                'keywords': ['cough', 'coughing', 'dry cough', 'wet cough', 'chest cough', 'throat cough'],
                'response': {
                    'en': """🫁 **Cough Information:**
                    
**Types:**
• **Dry cough:** No mucus, often irritating
• **Wet cough:** Produces mucus/phlegm

**Home Remedies:**
• Stay hydrated (warm water, tea)
• Honey (1-2 tsp, not for children <1 year)
• Steam inhalation
• Avoid irritants (smoke, dust)
• Elevate head while sleeping

**Medications:**
• Cough suppressants for dry cough
• Expectorants for wet cough
• Throat lozenges
• Warm salt water gargles

**When to see a doctor:**
• Cough lasting >3 weeks
• Blood in mucus
• Difficulty breathing
• Chest pain
• High fever with cough
• Wheezing sounds""",
                    'hi': """🫁 **खांसी की जानकारी:**
                    
**प्रकार:**
• **सूखी खांसी:** बलगम नहीं, अक्सर परेशान करने वाली
• **गीली खांसी:** बलगम/कफ पैदा करती है

**घरेलू उपचार:**
• हाइड्रेटेड रहें (गर्म पानी, चाय)
• शहद (1-2 चम्मच, 1 साल से कम उम्र के बच्चों के लिए नहीं)
• भाप लेना
• परेशान करने वाली चीजों से बचें (धुआं, धूल)
• सोते समय सिर ऊंचा रखें

**दवाएं:**
• सूखी खांसी के लिए खांसी दबाने वाली दवाएं
• गीली खांसी के लिए एक्सपेक्टोरेंट
• गले की गोलियां
• गर्म नमक के पानी से गरारे

**डॉक्टर से कब मिलें:**
• 3 सप्ताह से अधिक खांसी
• बलगम में खून
• सांस लेने में कठिनाई
• छाती में दर्द
• खांसी के साथ उच्च बुखार
• घरघराहट की आवाज"""
                }
            },
            
            # Malaria related
            'malaria': {
                'keywords': ['malaria', 'malarial fever', 'plasmodium', 'mosquito bite', 'chills and fever'],
                'response': {
                    'en': """🦟 **Malaria Information:**
                    
**Symptoms:**
• High fever with chills
• Sweating
• Headache
• Nausea and vomiting
• Muscle pain
• Fatigue

**Transmission:** Mosquito bite (Anopheles mosquito)

**Prevention:**
• Use mosquito nets
• Apply insect repellent
• Wear long sleeves/pants
• Eliminate standing water
• Use window screens

**Treatment:** Requires prescription medication (antimalarials)

**⚠️ Important:** Malaria can be life-threatening. If you suspect malaria, seek immediate medical attention.

**When to see a doctor immediately:**
• Fever with chills in malaria-endemic areas
• Any malaria symptoms
• Recent travel to malaria-prone regions""",
                    'hi': """🦟 **मलेरिया की जानकारी:**
                    
**लक्षण:**
• ठंड के साथ उच्च बुखार
• पसीना
• सिरदर्द
• मतली और उल्टी
• मांसपेशियों में दर्द
• थकान

**संचरण:** मच्छर का काटना (एनोफिलीज मच्छर)

**रोकथाम:**
• मच्छरदानी का उपयोग करें
• कीटनाशक लगाएं
• लंबी आस्तीन/पैंट पहनें
• खड़े पानी को खत्म करें
• खिड़की के जाली का उपयोग करें

**उपचार:** नुस्खे की दवा की आवश्यकता (एंटीमलेरियल)

**⚠️ महत्वपूर्ण:** मलेरिया जानलेवा हो सकता है। यदि आपको मलेरिया का संदेह है, तो तुरंत चिकित्सा सहायता लें।

**तुरंत डॉक्टर से कब मिलें:**
• मलेरिया-प्रभावित क्षेत्रों में ठंड के साथ बुखार
• कोई भी मलेरिया लक्षण
• मलेरिया-प्रवण क्षेत्रों की हाल की यात्रा"""
                }
            },
            
            # Diabetes related
            'diabetes': {
                'keywords': ['diabetes', 'diabetic', 'blood sugar', 'glucose', 'insulin', 'high sugar'],
                'response': {
                    'en': """🍯 **Diabetes Information:**
                    
**Types:**
• **Type 1:** Body doesn't produce insulin
• **Type 2:** Body doesn't use insulin properly
• **Gestational:** During pregnancy

**Common Symptoms:**
• Frequent urination
• Excessive thirst
• Unexplained weight loss
• Fatigue
• Blurred vision
• Slow healing wounds

**Management:**
• Regular blood sugar monitoring
• Healthy diet (low sugar, high fiber)
• Regular exercise
• Medication as prescribed
• Regular doctor visits

**⚠️ Emergency:** Very high or very low blood sugar can be dangerous.

**When to see a doctor:**
• Any diabetes symptoms
• Family history of diabetes
• Regular checkups if diagnosed""",
                    'hi': """🍯 **मधुमेह की जानकारी:**
                    
**प्रकार:**
• **टाइप 1:** शरीर इंसुलिन नहीं बनाता
• **टाइप 2:** शरीर इंसुलिन का सही उपयोग नहीं करता
• **गर्भावस्था:** गर्भावस्था के दौरान

**सामान्य लक्षण:**
• बार-बार पेशाब
• अत्यधिक प्यास
• बिना कारण वजन कम होना
• थकान
• धुंधली दृष्टि
• धीमी चिकित्सा

**प्रबंधन:**
• नियमित रक्त शर्करा निगरानी
• स्वस्थ आहार (कम चीनी, उच्च फाइबर)
• नियमित व्यायाम
• निर्धारित दवाएं
• नियमित डॉक्टर की जांच

**⚠️ आपातकाल:** बहुत अधिक या बहुत कम रक्त शर्करा खतरनाक हो सकता है।

**डॉक्टर से कब मिलें:**
• कोई भी मधुमेह लक्षण
• मधुमेह का पारिवारिक इतिहास
• निदान होने पर नियमित जांच"""
                }
            },
            
            # Tuberculosis related
            'tb': {
                'keywords': ['tuberculosis', 'tb', 'tuberculosis', 'pulmonary tb', 'lung infection', 'mycobacterium'],
                'response': {
                    'en': """🫁 **Tuberculosis (TB) Information:**
                    
**Symptoms:**
• Persistent cough (>3 weeks)
• Coughing up blood
• Chest pain
• Fatigue
• Weight loss
• Night sweats
• Fever

**Transmission:** Airborne (coughing, sneezing)

**Treatment:** Long-term antibiotic course (6+ months)

**Prevention:**
• BCG vaccination (in some countries)
• Good ventilation
• Cover mouth when coughing
• Complete treatment if diagnosed

**⚠️ Important:** TB is curable with proper treatment. Untreated TB can be fatal.

**When to see a doctor immediately:**
• Persistent cough with blood
• Any TB symptoms
• Contact with TB patient
• Unexplained weight loss with cough""",
                    'hi': """🫁 **क्षय रोग (टीबी) की जानकारी:**
                    
**लक्षण:**
• लगातार खांसी (>3 सप्ताह)
• खून की खांसी
• छाती में दर्द
• थकान
• वजन कम होना
• रात को पसीना
• बुखार

**संचरण:** हवा के माध्यम से (खांसना, छींकना)

**उपचार:** दीर्घकालिक एंटीबायोटिक कोर्स (6+ महीने)

**रोकथाम:**
• बीसीजी टीकाकरण (कुछ देशों में)
• अच्छा वेंटिलेशन
• खांसते समय मुंह ढकें
• निदान होने पर पूरा उपचार

**⚠️ महत्वपूर्ण:** टीबी उचित उपचार से ठीक हो सकता है। अनुपचारित टीबी घातक हो सकता है।

**तुरंत डॉक्टर से कब मिलें:**
• खून के साथ लगातार खांसी
• कोई भी टीबी लक्षण
• टीबी रोगी के संपर्क में
• खांसी के साथ बिना कारण वजन कम होना"""
                }
            },
            
            # Medicine information
            'paracetamol': {
                'keywords': ['paracetamol', 'acetaminophen', 'tylenol', 'calpol', 'dolo'],
                'response': {
                    'en': """💊 **Paracetamol Information:**
                    
**Uses:** Pain relief, fever reduction

**Dosage:**
• Adults: 500-1000mg every 6 hours
• Children: 10-15mg/kg every 6 hours
• Maximum: 4000mg per day (adults)

**Side Effects:**
• Rare when taken correctly
• Liver damage if overdose
• Allergic reactions (rare)

**Precautions:**
• Don't exceed recommended dose
• Avoid alcohol
• Check other medications for paracetamol
• Consult doctor if pregnant/breastfeeding

**⚠️ Warning:** Overdose can cause liver failure. Never exceed 4000mg/day.""",
                    'hi': """💊 **पैरासिटामोल की जानकारी:**
                    
**उपयोग:** दर्द से राहत, बुखार कम करना

**खुराक:**
• वयस्क: 500-1000mg हर 6 घंटे
• बच्चे: 10-15mg/kg हर 6 घंटे
• अधिकतम: 4000mg प्रति दिन (वयस्क)

**दुष्प्रभाव:**
• सही तरीके से लेने पर दुर्लभ
• अधिक मात्रा में लिवर क्षति
• एलर्जिक प्रतिक्रियाएं (दुर्लभ)

**सावधानियां:**
• अनुशंसित खुराक से अधिक न लें
• शराब से बचें
• अन्य दवाओं में पैरासिटामोल की जांच करें
• गर्भवती/स्तनपान कराने वाली महिलाएं डॉक्टर से सलाह लें

**⚠️ चेतावनी:** अधिक मात्रा लिवर फेल्योर का कारण बन सकती है। कभी भी 4000mg/दिन से अधिक न लें।"""
                }
            },
            
            'ibuprofen': {
                'keywords': ['ibuprofen', 'brufen', 'advil', 'motrin', 'nurofen'],
                'response': {
                    'en': """💊 **Ibuprofen Information:**
                    
**Uses:** Pain relief, inflammation reduction, fever reduction

**Dosage:**
• Adults: 200-400mg every 6-8 hours
• Children: 5-10mg/kg every 6-8 hours
• Maximum: 2400mg per day (adults)

**Side Effects:**
• Stomach upset
• Heartburn
• Dizziness
• Headache
• Increased bleeding risk

**Precautions:**
• Take with food
• Avoid if stomach ulcers
• Don't use if allergic to aspirin
• Consult doctor if pregnant/breastfeeding
• Monitor blood pressure

**⚠️ Warning:** Can cause stomach bleeding. Take with food.""",
                    'hi': """💊 **आइबुप्रोफेन की जानकारी:**
                    
**उपयोग:** दर्द से राहत, सूजन कम करना, बुखार कम करना

**खुराक:**
• वयस्क: 200-400mg हर 6-8 घंटे
• बच्चे: 5-10mg/kg हर 6-8 घंटे
• अधिकतम: 2400mg प्रति दिन (वयस्क)

**दुष्प्रभाव:**
• पेट में परेशानी
• सीने में जलन
• चक्कर आना
• सिरदर्द
• रक्तस्राव का खतरा बढ़ना

**सावधानियां:**
• भोजन के साथ लें
• पेट के अल्सर हो तो न लें
• एस्पिरिन से एलर्जी हो तो न लें
• गर्भवती/स्तनपान कराने वाली महिलाएं डॉक्टर से सलाह लें
• रक्तचाप की निगरानी करें

**⚠️ चेतावनी:** पेट में रक्तस्राव का कारण बन सकता है। भोजन के साथ लें।"""
                }
            },
            
            'antibiotics': {
                'keywords': ['antibiotics', 'antibiotic', 'amoxicillin', 'azithromycin', 'ciprofloxacin', 'penicillin'],
                'response': {
                    'en': """💊 **Antibiotics Information:**
                    
**Important:** Antibiotics require prescription and should only be taken as directed by a doctor.

**Common Types:**
• Amoxicillin
• Azithromycin
• Ciprofloxacin
• Penicillin

**Key Points:**
• Complete the full course even if feeling better
• Don't share antibiotics
• Don't use leftover antibiotics
• Take at regular intervals
• Some require food, others on empty stomach

**Side Effects:**
• Nausea
• Diarrhea
• Allergic reactions
• Yeast infections (women)

**⚠️ Critical:** 
• Antibiotic resistance is a serious problem
• Only take when prescribed by a doctor
• Never self-medicate with antibiotics""",
                    'hi': """💊 **एंटीबायोटिक्स की जानकारी:**
                    
**महत्वपूर्ण:** एंटीबायोटिक्स के लिए नुस्खे की आवश्यकता होती है और केवल डॉक्टर के निर्देशानुसार लेना चाहिए।

**सामान्य प्रकार:**
• एमोक्सिसिलिन
• एजिथ्रोमाइसिन
• सिप्रोफ्लॉक्सासिन
• पेनिसिलिन

**मुख्य बिंदु:**
• बेहतर महसूस करने पर भी पूरा कोर्स पूरा करें
• एंटीबायोटिक्स साझा न करें
• बचे हुए एंटीबायोटिक्स का उपयोग न करें
• नियमित अंतराल पर लें
• कुछ को भोजन के साथ, कुछ को खाली पेट लेना होता है

**दुष्प्रभाव:**
• मतली
• दस्त
• एलर्जिक प्रतिक्रियाएं
• यीस्ट संक्रमण (महिलाएं)

**⚠️ महत्वपूर्ण:**
• एंटीबायोटिक प्रतिरोध एक गंभीर समस्या है
• केवल डॉक्टर के नुस्खे पर लें
• कभी भी एंटीबायोटिक्स से स्व-चिकित्सा न करें"""
                }
            }
        }
        
        # Default response for unknown queries
        self.default_response = {
            'en': "I'm not sure about that. Please consult a doctor or visit the nearest hospital for accurate advice.",
            'hi': "मुझे इसके बारे में निश्चित नहीं है। सटीक सलाह के लिए कृपया डॉक्टर से सलाह लें या निकटतम अस्पताल जाएं।"
        }
    
    def find_matching_topic(self, user_input):
        """Find the best matching health topic based on user input"""
        user_input_lower = user_input.lower()
        
        # Check each topic's keywords
        for topic, data in self.health_knowledge.items():
            for keyword in data['keywords']:
                if keyword.lower() in user_input_lower:
                    return topic
        
        return None
    
    def get_response(self, user_input, language='en'):
        """Get appropriate response for user input"""
        try:
            topic = self.find_matching_topic(user_input)
            
            if topic:
                return self.health_knowledge[topic]['response'].get(language, self.health_knowledge[topic]['response']['en'])
            else:
                return self.default_response.get(language, self.default_response['en'])
        except Exception as e:
            print(f"Error getting response: {str(e)}")
            return self.default_response.get(language, self.default_response['en'])
    
    def add_new_topic(self, topic_name, keywords, response_en, response_hi=None):
        """Add a new health topic to the knowledge base"""
        self.health_knowledge[topic_name] = {
            'keywords': keywords,
            'response': {
                'en': response_en,
                'hi': response_hi or response_en
            }
        }

def main():
    st.set_page_config(
        page_title="Health Chatbot - Arogya Mitra",
        page_icon="🤖",
        layout="wide"
    )
    
    # Initialize chatbot
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = HealthChatbot()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    
    # Header
    st.title("🤖 Health Chatbot")
    st.markdown("Ask me about common health topics like fever, cold, cough, diabetes, and medicines!")
    
    # Language selection
    col1, col2 = st.columns([1, 4])
    with col1:
        language = st.selectbox("Language", ["English", "हिंदी"], index=0)
        st.session_state.language = 'en' if language == "English" else 'hi'
    
    with col2:
        st.info("💡 **Tip:** I can help with fever, cold, cough, malaria, diabetes, TB, and common medicines like paracetamol, ibuprofen, and antibiotics.")
    
    # Chat interface
    st.subheader("💬 Chat with Health Bot")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, (timestamp, user_msg, bot_response) in enumerate(st.session_state.chat_history):
            with st.chat_message("user"):
                st.write(f"**You:** {user_msg}")
                st.caption(f"🕐 {timestamp}")
            
            with st.chat_message("assistant"):
                st.markdown(bot_response)
    
    # Input form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Ask your health question:",
            placeholder="e.g., I have fever and headache, what should I do?",
            key="user_input"
        )
        
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            submit_button = st.form_submit_button("Send", use_container_width=True)
        with col2:
            clear_button = st.form_submit_button("Clear Chat", use_container_width=True)
        
        if clear_button:
            st.session_state.chat_history = []
            st.rerun()
        
        if submit_button and user_input.strip():
            # Get bot response
            bot_response = st.session_state.chatbot.get_response(user_input, st.session_state.language)
            
            # Add to chat history
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.chat_history.append((timestamp, user_input, bot_response))
            
            st.rerun()
    
    # Quick action buttons
    st.subheader("🚀 Quick Health Topics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    quick_topics = [
        ("Fever", "fever"),
        ("Cold", "cold"),
        ("Cough", "cough"),
        ("Diabetes", "diabetes")
    ]
    
    for i, (display_name, topic) in enumerate(quick_topics):
        with [col1, col2, col3, col4][i]:
            if st.button(f"🤒 {display_name}", use_container_width=True):
                # Simulate user input for quick topic
                user_input = f"I have {topic}"
                bot_response = st.session_state.chatbot.get_response(user_input, st.session_state.language)
                timestamp = datetime.now().strftime("%H:%M:%S")
                st.session_state.chat_history.append((timestamp, user_input, bot_response))
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p><strong>⚠️ Disclaimer:</strong> This chatbot provides general health information only. 
        It is not a substitute for professional medical advice, diagnosis, or treatment. 
        Always consult a qualified healthcare provider for medical concerns.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
