"""General education and faithful score interpretation, not image findings."""
from translations import CATALOG, t

CLASS_INFO = {
    'BCC': ('Basal cell carcinoma',
            'BCC is a skin cancer that starts in the lower part of the epidermis, the outer skin layer.',
            'General signs can include a shiny lump, a scaly patch or a sore that does not heal.'),
    'Melanoma': ('Melanoma',
                 'Melanoma is a skin cancer that starts in pigment-producing cells called melanocytes.',
                 'General warning signs include an uneven shape or border, varied colour, or a mole or spot that changes over time.'),
    'SCC': ('Squamous cell carcinoma',
            'SCC is a skin cancer that starts in squamous cells near the surface of the skin.',
            'General signs can include a firm lump, a rough scaly patch or an open sore that bleeds.'),
}
ABOUT = 'About the suspected class'
WHY = 'Why this class was suggested'
GENERAL_ONLY = 'These are general descriptions, not findings detected in this image. Appearance can vary and other conditions can look similar.'
SCORE_REASON = 'The saved model gave {label} a score of {score:.1%}, the highest score among BCC, Melanoma and SCC. The app uses the highest-scoring class as its suggestion.'
TIED_REASON = 'The saved model gave {label} a score of {score:.1%}, tied for the highest score. The saved class follows the model output order; a tie does not favour one diagnosis.'
LIMIT = 'This explains the score-based selection, not which image features caused it. This model does not report verified borders, colours, textures or a lesion location. Scores are uncalibrated and are not the probability that the patient has cancer.'
CLOSED_SET = 'The model only compares these three cancer classes. It has no normal-skin or benign class, so a high score cannot confirm that cancer or even a lesion is present.'
SOURCES = (
    ('NCI Skin cancer definition', 'https://www.cancer.gov/publications/dictionaries/cancer-terms/def/skin-cancer'),
    ('CDC Symptoms of skin cancer', 'https://www.cdc.gov/skin-cancer/symptoms/index.html'),
)

CATALOG.update({
    ABOUT: 'Kuhusu aina inayoshukiwa',
    WHY: 'Kwa nini aina hii imependekezwa',
    'Basal cell carcinoma': 'Saratani ya seli za msingi',
    'Squamous cell carcinoma': 'Saratani ya seli bapa',
    CLASS_INFO['BCC'][1]: 'BCC ni saratani ya ngozi inayoanzia sehemu ya chini ya tabaka la nje la ngozi.',
    CLASS_INFO['BCC'][2]: 'Dalili za jumla zinaweza kuwa uvimbe unaongaa, eneo lenye magamba au kidonda kisichopona.',
    CLASS_INFO['Melanoma'][1]: 'Melanoma ni saratani ya ngozi inayoanzia seli zinazotengeneza rangi ya ngozi zinazoitwa melanocytes.',
    CLASS_INFO['Melanoma'][2]: 'Dalili za jumla za tahadhari ni umbo au mipaka isiyo sawa, rangi tofauti, au fuko au doa linalobadilika kadiri muda unavyopita.',
    CLASS_INFO['SCC'][1]: 'SCC ni saratani ya ngozi inayoanzia seli bapa karibu na uso wa ngozi.',
    CLASS_INFO['SCC'][2]: 'Dalili za jumla zinaweza kuwa uvimbe mgumu, eneo lenye magamba au kidonda kinachotoka damu.',
    GENERAL_ONLY: 'Haya ni maelezo ya jumla, si dalili zilizogunduliwa katika picha hii. Mwonekano unaweza kutofautiana na hali nyingine zinaweza kufanana.',
    SCORE_REASON: 'Modeli iliyohifadhiwa iliipa {label} alama ya {score:.1%}, alama ya juu zaidi kati ya BCC, Melanoma na SCC. Programu inapendekeza aina yenye alama ya juu zaidi.',
    TIED_REASON: 'Modeli iliyohifadhiwa iliipa {label} alama ya {score:.1%}, ikiwa sawa na alama nyingine ya juu zaidi. Aina iliyohifadhiwa inafuata mpangilio wa matokeo ya modeli; usawa huo haupendelei utambuzi mmoja.',
    LIMIT: 'Haya yanaeleza uteuzi unaotegemea alama, si vipengele vya picha vilivyosababisha uteuzi huo. Modeli hii haitoi mipaka, rangi, muundo au eneo la kidonda vilivyothibitishwa. Alama hazijarekebishwa kuwa makadirio ya uwezekano na si uwezekano wa mgonjwa kuwa na saratani.',
    CLOSED_SET: 'Modeli inalinganisha aina hizi tatu za saratani pekee. Haina aina ya ngozi ya kawaida au hali isiyo saratani, kwa hivyo alama ya juu haiwezi kuthibitisha saratani au hata kuwepo kwa kidonda.',
    'Download referral checklist as Word': 'Pakua orodha ya rufaa kama Word',
    'Clinical assessment and referral checklist': 'Orodha ya tathmini ya kitabibu na rufaa',
    'Prediction summary': 'Muhtasari wa utabiri',
    'Referral and follow up': 'Rufaa na ufuatiliaji',
    'Educational sources': 'Vyanzo vya elimu',
    'Class': 'Aina',
    'Score': 'Alama',
    'Decision support only': 'Msaada wa kufanya maamuzi pekee',
})


def interpretation(prediction):
    label = prediction['cancer_class']
    scores = prediction['scores']
    top = max(scores.values())
    tied = sum(abs(v - top) < 1e-9 for v in scores.values()) > 1
    return t(TIED_REASON if tied else SCORE_REASON).format(label=label, score=scores[label])


def show_classification_info(prediction):
    import streamlit as st
    name, description, signs = CLASS_INFO[prediction['cancer_class']]
    st.subheader(t(ABOUT))
    st.write(t(name))
    st.write(t(description))
    st.write(t(signs))
    st.caption(t(GENERAL_ONLY))
    with st.expander(t(WHY), expanded=True):
        st.write(interpretation(prediction))
        st.write(t(LIMIT))
        st.caption(t(CLOSED_SET))
    with st.expander(t('Educational sources')):
        for title, url in SOURCES:
            st.markdown(f'[{title}]({url})')
