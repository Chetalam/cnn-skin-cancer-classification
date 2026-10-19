"""English/Kiswahili display translations. Stored codes and user data stay unchanged."""
import re
import streamlit as st

CATALOG = {'Dashboard': 'Dashibodi',
 'Administrator dashboard': 'Dashibodi ya msimamizi',
 'Healthcare Worker dashboard': 'Dashibodi ya mhudumu wa afya',
 'System Administrator': 'Msimamizi wa Mfumo',
 'Healthcare Worker': 'Mhudumu wa Afya',
 'Analyse Image': 'Changanua Picha',
 'History': 'Historia',
 'Account': 'Akaunti',
 'Help': 'Msaada',
 'Welcome': 'Karibu',
 'Welcome / Sign in': 'Karibu / Ingia',
 'User Management': 'Usimamizi wa Watumiaji',
 'Dataset Status': 'Hali ya Seti za Data',
 'Database Guide': 'Mwongozo wa Hifadhidata',
 'Review Records': 'Rekodi za Mapitio',
 'Log out': 'Ondoka',
 'Sign in': 'Ingia',
 'Create account': 'Fungua akaunti',
 'Full name': 'Jina kamili',
 'Email address': 'Anwani ya barua pepe',
 'Password': 'Nenosiri',
 'Current password': 'Nenosiri la sasa',
 'New password': 'Nenosiri jipya',
 'Confirm password': 'Thibitisha nenosiri',
 'Confirm new password': 'Thibitisha nenosiri jipya',
 'Healthcare centre name': 'Jina la kituo cha afya',
 'Which account are you creating?': 'Unafungua akaunti ya aina gani?',
 'Welcome to SkinCare Research': 'Karibu SkinCare Research',
 'A workspace for skin lesion image review and CNN classification research.': 'Sehemu ya kupitia '
                                                                              'picha za mabadiliko '
                                                                              'ya ngozi na kufanya '
                                                                              'utafiti wa '
                                                                              'uainishaji kwa CNN.',
 'Register or sign in to access your dashboard. Predictions will become available after model integration.': 'Fungua '
                                                                                                             'akaunti '
                                                                                                             'au '
                                                                                                             'ingia '
                                                                                                             'ili '
                                                                                                             'kufikia '
                                                                                                             'dashibodi '
                                                                                                             'yako. '
                                                                                                             'Matokeo '
                                                                                                             'ya '
                                                                                                             'modeli '
                                                                                                             'yatapatikana '
                                                                                                             'baada '
                                                                                                             'ya '
                                                                                                             'modeli '
                                                                                                             'kuunganishwa.',
 'Email verification and password-reset emails are not enabled in this prototype.': 'Uthibitishaji '
                                                                                    'wa barua pepe '
                                                                                    'na ujumbe wa '
                                                                                    'kuweka upya '
                                                                                    'nenosiri '
                                                                                    'haujawezeshwa '
                                                                                    'katika toleo '
                                                                                    'hili la '
                                                                                    'majaribio.',
 'Both account roles are active immediately after registration. No invitation or approval is required.': 'Aina '
                                                                                                         'zote '
                                                                                                         'mbili '
                                                                                                         'za '
                                                                                                         'akaunti '
                                                                                                         'zinaanza '
                                                                                                         'kutumika '
                                                                                                         'mara '
                                                                                                         'baada '
                                                                                                         'ya '
                                                                                                         'usajili. '
                                                                                                         'Mwaliko '
                                                                                                         'wala '
                                                                                                         'idhini '
                                                                                                         'haihitajiki.',
 'I already have a Healthcare Worker account and am creating my separate System Administrator account.': 'Tayari '
                                                                                                         'nina '
                                                                                                         'akaunti '
                                                                                                         'ya '
                                                                                                         'Mhudumu '
                                                                                                         'wa '
                                                                                                         'Afya '
                                                                                                         'na '
                                                                                                         'ninafungua '
                                                                                                         'akaunti '
                                                                                                         'yangu '
                                                                                                         'tofauti '
                                                                                                         'ya '
                                                                                                         'Msimamizi '
                                                                                                         'wa '
                                                                                                         'Mfumo.',
 'Use a password or passphrase with 12–128 characters.': 'Tumia nenosiri au kirai cha siri chenye '
                                                         'herufi 12–128.',
 '**Verify your existing Healthcare Worker account**': '**Thibitisha akaunti yako iliyopo ya '
                                                       'Mhudumu wa Afya**',
 'Your new account must use a different email address and password.': 'Akaunti yako mpya lazima '
                                                                      'itumie barua pepe na '
                                                                      'nenosiri tofauti.',
 'Existing account email address': 'Barua pepe ya akaunti iliyopo',
 'Existing account password': 'Nenosiri la akaunti iliyopo',
 'I understand this is a research prototype and will use de-identified images.': 'Ninaelewa kuwa '
                                                                                 'huu ni mfumo wa '
                                                                                 'majaribio wa '
                                                                                 'utafiti na '
                                                                                 'nitatumia picha '
                                                                                 'zisizo na '
                                                                                 'taarifa '
                                                                                 'zinazomtambulisha '
                                                                                 'mtu.',
 'Please acknowledge the research-use notice.': 'Tafadhali thibitisha kuwa umeelewa taarifa ya '
                                                'matumizi ya utafiti.',
 'The passwords do not match.': 'Manenosiri hayalingani.',
 'Enter your existing account email and password.': 'Weka barua pepe na nenosiri la akaunti yako '
                                                    'iliyopo.',
 'Healthcare centre names are self-declared.': 'Majina ya vituo vya afya hutolewa na watumiaji '
                                               'wenyewe.',
 'No clinical diagnosis is provided at this milestone.': 'Mfumo hautoi utambuzi wa kitabibu katika '
                                                         'hatua hii.',
 'Your research workspace': 'Sehemu yako ya utafiti',
 'Sign-in could not be completed.': 'Kuingia hakukukamilika.',
 '**Account role:** ': '**Aina ya akaunti:** ',
 '**Healthcare centre:** ': '**Kituo cha afya:** ',
 'Account role:': 'Aina ya akaunti:',
 'Healthcare centre:': 'Kituo cha afya:',
 'Users at your healthcare centre': 'Watumiaji katika kituo chako cha afya',
 'Name': 'Jina',
 'Email': 'Barua pepe',
 'Email:': 'Barua pepe:',
 'Role': 'Aina ya akaunti',
 'Status': 'Hali',
 'Status:': 'Hali:',
 'Registered': 'Tarehe ya usajili',
 'Deactivated': 'Imezimwa',
 'Active': 'Inatumika',
 'Suspended': 'Imesimamishwa',
 'Pending': 'Inasubiri',
 'Rejected': 'Imekataliwa',
 'active': 'Inatumika',
 'suspended': 'Imesimamishwa',
 'deactivated': 'Imezimwa',
 'pending': 'Inasubiri',
 'rejected': 'Imekataliwa',
 'Not provided': 'Haijatolewa',
 'No other users are registered at your healthcare centre.': 'Hakuna watumiaji wengine '
                                                             'waliosajiliwa katika kituo chako cha '
                                                             'afya.',
 'Use User Management in the sidebar to suspend or reactivate accounts.': 'Tumia Usimamizi wa '
                                                                          'Watumiaji kwenye menyu '
                                                                          'ya pembeni kusimamisha '
                                                                          'au kuwezesha akaunti '
                                                                          'tena.',
 'Your saved reviews': 'Mapitio yako yaliyohifadhiwa',
 'Your completed predictions': 'Matokeo yako ya modeli yaliyokamilika',
 'Your reviews awaiting model': 'Mapitio yako yanayosubiri modeli',
 'Start a review': 'Anza kupitia picha',
 'Upload a de-identified lesion image, check the preview and save a review.': 'Pakia picha ya '
                                                                              'badiliko la ngozi '
                                                                              'isiyo na taarifa za '
                                                                              'utambulisho, kagua '
                                                                              'mwonekano na '
                                                                              'uhifadhi mapitio.',
 'Open Analyse Image': 'Fungua Changanua Picha',
 'The CNN is not integrated. Newly saved reviews await the model and have no predicted class or confidence.': 'CNN '
                                                                                                              'haijaunganishwa. '
                                                                                                              'Mapitio '
                                                                                                              'mapya '
                                                                                                              'yanasubiri '
                                                                                                              'modeli '
                                                                                                              'na '
                                                                                                              'hayana '
                                                                                                              'aina '
                                                                                                              'iliyotabiriwa '
                                                                                                              'wala '
                                                                                                              'alama '
                                                                                                              'ya '
                                                                                                              'uhakika.',
 'Your recent reviews': 'Mapitio yako ya hivi karibuni',
 'Case reference': 'Rejea ya kisa',
 'File': 'Faili',
 'Saved': 'Tarehe ya kuhifadhi',
 'Awaiting model': 'Inasubiri modeli',
 'Predicted': 'Imetabiriwa',
 'Unavailable': 'Haipatikani',
 'No reviews yet. Your first saved review will appear here.': 'Bado hakuna mapitio. Mapitio yako '
                                                              'ya kwanza yaliyohifadhiwa '
                                                              'yataonekana hapa.',
 'Analyse a skin lesion image': 'Changanua picha ya badiliko la ngozi',
 '1. Upload and preview': '1. Pakia na uangalie picha',
 'Choose a JPG or PNG image': 'Chagua picha ya JPG au PNG',
 'Maximum 10 MB and 20 million pixels. Use a de-identified image.': 'Kiwango cha juu ni MB 10 na '
                                                                    'pikseli milioni 20. Tumia '
                                                                    'picha isiyo na taarifa za '
                                                                    'utambulisho.',
 'Image is readable.': 'Picha inaweza kusomwa.',
 'Choose an image to begin.': 'Chagua picha ili kuanza.',
 '2. Save a review': '2. Hifadhi mapitio',
 'Optional case reference': 'Rejea ya kisa (si lazima)',
 'Use an anonymous reference, not a patient name or ID.': 'Tumia rejea isiyomtambulisha mtu, wala '
                                                          'si jina au kitambulisho cha mgonjwa.',
 'Save a small preview and file metadata in my history.': 'Hifadhi picha ndogo na taarifa za faili '
                                                          'katika historia yangu.',
 'The original image is not stored. A preview up to 320 × 320 pixels is retained when saved.': 'Picha '
                                                                                               'ya '
                                                                                               'asili '
                                                                                               'haihifadhiwi. '
                                                                                               'Picha '
                                                                                               'ndogo '
                                                                                               'ya '
                                                                                               'hadi '
                                                                                               'pikseli '
                                                                                               '320 '
                                                                                               '× '
                                                                                               '320 '
                                                                                               'huhifadhiwa '
                                                                                               'unapohifadhi '
                                                                                               'mapitio.',
 'Save review': 'Hifadhi mapitio',
 'Review saved to your history.': 'Mapitio yamehifadhiwa katika historia yako.',
 'Awaiting model integration. Classification was not performed.': 'Inasubiri modeli kuunganishwa. '
                                                                  'Uainishaji haujafanywa.',
 'View saved history': 'Angalia historia iliyohifadhiwa',
 'Predictions remain unavailable until model integration.': 'Matokeo ya modeli hayatapatikana hadi '
                                                            'modeli iunganishwe.',
 'Readability validation cannot confirm that the image depicts a skin lesion.': 'Ukaguzi wa '
                                                                                'kusomeka kwa '
                                                                                'picha hauwezi '
                                                                                'kuthibitisha kuwa '
                                                                                'picha inaonyesha '
                                                                                'badiliko la '
                                                                                'ngozi.',
 'Your review history': 'Historia ya mapitio yako',
 'No saved reviews yet.': 'Bado hakuna mapitio yaliyohifadhiwa.',
 'Upload your first image': 'Pakia picha yako ya kwanza',
 'Record': 'Rekodi',
 'Class': 'Aina',
 'Confidence': 'Alama ya uhakika',
 'Download my history as CSV': 'Pakua historia yangu kama CSV',
 'Open a saved review': 'Fungua mapitio yaliyohifadhiwa',
 'Stored preview': 'Picha ndogo iliyohifadhiwa',
 'Original dimensions:': 'Vipimo vya picha ya asili:',
 'Research record. No clinical diagnosis is implied.': 'Rekodi ya utafiti. Haimaanishi kuwa '
                                                       'utambuzi wa kitabibu umefanywa.',
 'Delete this saved review and its preview permanently.': 'Futa kabisa mapitio haya na picha yake '
                                                          'ndogo.',
 'Delete review': 'Futa mapitio',
 'Review deleted.': 'Mapitio yamefutwa.',
 'Account settings': 'Mipangilio ya akaunti',
 'Profile': 'Wasifu',
 'Change password': 'Badilisha nenosiri',
 'Deactivate profile': 'Zima wasifu',
 'Enter your healthcare centre name and save your profile to continue.': 'Weka jina la kituo chako '
                                                                         'cha afya na uhifadhi '
                                                                         'wasifu wako ili '
                                                                         'kuendelea.',
 'Save profile': 'Hifadhi wasifu',
 'Profile updated.': 'Wasifu umesasishwa.',
 "Your centre name does not grant access to other users' saved reviews.": 'Jina la kituo chako '
                                                                          'halikupi ruhusa ya '
                                                                          'kufikia mapitio ya '
                                                                          'watumiaji wengine.',
 'Use 12–128 characters. Linked accounts for different roles must use different passwords.': 'Tumia '
                                                                                             'herufi '
                                                                                             '12–128. '
                                                                                             'Akaunti '
                                                                                             'zilizounganishwa '
                                                                                             'za '
                                                                                             'majukumu '
                                                                                             'tofauti '
                                                                                             'lazima '
                                                                                             'zitumie '
                                                                                             'manenosiri '
                                                                                             'tofauti.',
 'The new passwords do not match.': 'Manenosiri mapya hayalingani.',
 'Password changed. Sign in again.': 'Nenosiri limebadilishwa. Ingia tena.',
 'Deactivation prevents sign-in and ends all sessions for this account. Your profile and saved reviews stay in the database.': 'Kuzima '
                                                                                                                               'wasifu '
                                                                                                                               'kunazuia '
                                                                                                                               'kuingia '
                                                                                                                               'na '
                                                                                                                               'kufunga '
                                                                                                                               'vipindi '
                                                                                                                               'vyote '
                                                                                                                               'vya '
                                                                                                                               'akaunti '
                                                                                                                               'hii. '
                                                                                                                               'Wasifu '
                                                                                                                               'na '
                                                                                                                               'mapitio '
                                                                                                                               'yako '
                                                                                                                               'yanabaki '
                                                                                                                               'katika '
                                                                                                                               'hifadhidata.',
 'To reactivate your profile, contact an active administrator at your healthcare centre. Deactivation does not affect a separate account you hold for another role.': 'Ili '
                                                                                                                                                                      'kuwezesha '
                                                                                                                                                                      'wasifu '
                                                                                                                                                                      'tena, '
                                                                                                                                                                      'wasiliana '
                                                                                                                                                                      'na '
                                                                                                                                                                      'msimamizi '
                                                                                                                                                                      'mwenye '
                                                                                                                                                                      'akaunti '
                                                                                                                                                                      'inayotumika '
                                                                                                                                                                      'katika '
                                                                                                                                                                      'kituo '
                                                                                                                                                                      'chako. '
                                                                                                                                                                      'Kuzima '
                                                                                                                                                                      'wasifu '
                                                                                                                                                                      'hakuathiri '
                                                                                                                                                                      'akaunti '
                                                                                                                                                                      'yako '
                                                                                                                                                                      'tofauti '
                                                                                                                                                                      'ya '
                                                                                                                                                                      'jukumu '
                                                                                                                                                                      'jingine.',
 'Another active administrator at your centre must remain available.': 'Lazima kuwe na msimamizi '
                                                                       'mwingine mwenye akaunti '
                                                                       'inayotumika katika kituo '
                                                                       'chako.',
 'Enter your current password': 'Weka nenosiri lako la sasa',
 'I understand that my data will be retained and an administrator is needed to reactivate my account.': 'Ninaelewa '
                                                                                                        'kuwa '
                                                                                                        'data '
                                                                                                        'yangu '
                                                                                                        'itabaki '
                                                                                                        'na '
                                                                                                        'nitahitaji '
                                                                                                        'msimamizi '
                                                                                                        'kuwezesha '
                                                                                                        'akaunti '
                                                                                                        'yangu '
                                                                                                        'tena.',
 'Deactivate my profile': 'Zima wasifu wangu',
 'Confirm that you understand deactivation before continuing.': 'Thibitisha kuwa unaelewa kuzimwa '
                                                                'kwa wasifu kabla ya kuendelea.',
 'Your profile is deactivated. Your saved data has been retained.': 'Wasifu wako umezimwa. Data '
                                                                    'yako iliyohifadhiwa '
                                                                    'imebakizwa.',
 'Dataset and database status': 'Hali ya seti za data na hifadhidata',
 'Track the cleaned training manifest separately from uploaded application images.': 'Fuatilia '
                                                                                     'orodha ya '
                                                                                     'data ya '
                                                                                     'mafunzo '
                                                                                     'iliyosafishwa '
                                                                                     'kando na '
                                                                                     'picha '
                                                                                     'zilizopakiwa '
                                                                                     'kwenye '
                                                                                     'programu.',
 'Imported cleaned images': 'Picha zilizoorodheshwa katika data safi iliyoingizwa',
 'No cleaned manifest imported into the application database yet.': 'Bado hakuna orodha safi ya '
                                                                    'data iliyoingizwa katika '
                                                                    'hifadhidata ya programu.',
 'Notebook result: 2,703 cleaned records (1,165 Melanoma, 1,353 BCC, 185 SCC). App totals are shown only after import.': 'Matokeo '
                                                                                                                         'ya '
                                                                                                                         'daftari: '
                                                                                                                         'rekodi '
                                                                                                                         'safi '
                                                                                                                         '2,703 '
                                                                                                                         '(Melanoma '
                                                                                                                         '1,165, '
                                                                                                                         'BCC '
                                                                                                                         '1,353, '
                                                                                                                         'SCC '
                                                                                                                         '185). '
                                                                                                                         'Jumla '
                                                                                                                         'za '
                                                                                                                         'programu '
                                                                                                                         'huonekana '
                                                                                                                         'baada '
                                                                                                                         'ya '
                                                                                                                         'kuingiza '
                                                                                                                         'data.',
 'Import cleaned manifest': 'Ingiza orodha safi ya data',
 'Database checks': 'Ukaguzi wa hifadhidata',
 'Download Datasets/Cleaned/clean_metadata.csv from your Gmail Drive, then select it here.': 'Pakua '
                                                                                             'Datasets/Cleaned/clean_metadata.csv '
                                                                                             'kutoka '
                                                                                             'Google '
                                                                                             'Drive '
                                                                                             'yako, '
                                                                                             'kisha '
                                                                                             'uchague '
                                                                                             'hapa.',
 'Clean metadata CSV': 'CSV ya taarifa safi za data',
 'Replace the app’s previous manifest with this file. Original datasets and skin_cancer.db stay unchanged.': 'Badilisha '
                                                                                                             'orodha '
                                                                                                             'ya '
                                                                                                             'awali '
                                                                                                             'ya '
                                                                                                             'programu '
                                                                                                             'kwa '
                                                                                                             'faili '
                                                                                                             'hii. '
                                                                                                             'Seti '
                                                                                                             'za '
                                                                                                             'data '
                                                                                                             'za '
                                                                                                             'asili '
                                                                                                             'na '
                                                                                                             'skin_cancer.db '
                                                                                                             'hazitabadilishwa.',
 'Import manifest': 'Ingiza orodha ya data',
 'Import validates metadata and unique hashes. It cannot verify Drive image paths from your Windows computer and does not copy images.': 'Uingizaji '
                                                                                                                                         'hukagua '
                                                                                                                                         'taarifa '
                                                                                                                                         'za '
                                                                                                                                         'data '
                                                                                                                                         'na '
                                                                                                                                         'alama '
                                                                                                                                         'bainifu '
                                                                                                                                         'za '
                                                                                                                                         'picha. '
                                                                                                                                         'Hauwezi '
                                                                                                                                         'kuthibitisha '
                                                                                                                                         'njia '
                                                                                                                                         'za '
                                                                                                                                         'picha '
                                                                                                                                         'za '
                                                                                                                                         'Drive '
                                                                                                                                         'kutoka '
                                                                                                                                         'kompyuta '
                                                                                                                                         'yako '
                                                                                                                                         'ya '
                                                                                                                                         'Windows, '
                                                                                                                                         'wala '
                                                                                                                                         'haunakili '
                                                                                                                                         'picha.',
 'SQLite integrity and foreign-key checks passed.': 'Ukaguzi wa uadilifu wa SQLite na uhusiano wa '
                                                    'rekodi umefaulu.',
 'Database checks need investigation.': 'Matokeo ya ukaguzi wa hifadhidata yanahitaji kuchunguzwa.',
 'Schema version:': 'Toleo la muundo wa hifadhidata:',
 'Table': 'Jedwali',
 'Rows': 'Rekodi',
 'The model tables remain empty until trained models are registered. Pending reviews correctly contain no class or confidence.': 'Majedwali '
                                                                                                                                 'ya '
                                                                                                                                 'modeli '
                                                                                                                                 'yatabaki '
                                                                                                                                 'tupu '
                                                                                                                                 'hadi '
                                                                                                                                 'modeli '
                                                                                                                                 'zilizopewa '
                                                                                                                                 'mafunzo '
                                                                                                                                 'zisajiliwe. '
                                                                                                                                 'Mapitio '
                                                                                                                                 'yanayosubiri '
                                                                                                                                 'hayana '
                                                                                                                                 'aina '
                                                                                                                                 'wala '
                                                                                                                                 'alama '
                                                                                                                                 'ya '
                                                                                                                                 'uhakika.',
 'Only the project system_administrator can import datasets or inspect database internals.': 'Ni '
                                                                                             'Msimamizi '
                                                                                             'wa '
                                                                                             'Mfumo '
                                                                                             'pekee '
                                                                                             'anayeweza '
                                                                                             'kuingiza '
                                                                                             'seti '
                                                                                             'za '
                                                                                             'data '
                                                                                             'au '
                                                                                             'kukagua '
                                                                                             'hifadhidata.',
 'Account and sign-in': 'Akaunti na kuingia',
 'Use Account to edit your name and centre or change your password. Changing your password ends all sessions for that account. Email verification and password-reset emails are not enabled.': 'Tumia '
                                                                                                                                                                                               'Akaunti '
                                                                                                                                                                                               'kuhariri '
                                                                                                                                                                                               'jina '
                                                                                                                                                                                               'na '
                                                                                                                                                                                               'kituo '
                                                                                                                                                                                               'au '
                                                                                                                                                                                               'kubadilisha '
                                                                                                                                                                                               'nenosiri. '
                                                                                                                                                                                               'Kubadilisha '
                                                                                                                                                                                               'nenosiri '
                                                                                                                                                                                               'hufunga '
                                                                                                                                                                                               'vipindi '
                                                                                                                                                                                               'vyote '
                                                                                                                                                                                               'vya '
                                                                                                                                                                                               'akaunti '
                                                                                                                                                                                               'hiyo. '
                                                                                                                                                                                               'Uthibitishaji '
                                                                                                                                                                                               'wa '
                                                                                                                                                                                               'barua '
                                                                                                                                                                                               'pepe '
                                                                                                                                                                                               'na '
                                                                                                                                                                                               'ujumbe '
                                                                                                                                                                                               'wa '
                                                                                                                                                                                               'kuweka '
                                                                                                                                                                                               'upya '
                                                                                                                                                                                               'nenosiri '
                                                                                                                                                                                               'haujawezeshwa.',
 'Deactivation and reactivation': 'Kuzima na kuwezesha akaunti tena',
 'Open Account → Deactivate profile. Enter your current password and confirm. Your profile and reviews remain saved. An active administrator at your centre can reactivate your account. The last active administrator at a centre cannot self-deactivate.': 'Fungua '
                                                                                                                                                                                                                                                             'Akaunti '
                                                                                                                                                                                                                                                             '→ '
                                                                                                                                                                                                                                                             'Zima '
                                                                                                                                                                                                                                                             'wasifu. '
                                                                                                                                                                                                                                                             'Weka '
                                                                                                                                                                                                                                                             'nenosiri '
                                                                                                                                                                                                                                                             'la '
                                                                                                                                                                                                                                                             'sasa '
                                                                                                                                                                                                                                                             'na '
                                                                                                                                                                                                                                                             'uthibitishe. '
                                                                                                                                                                                                                                                             'Wasifu '
                                                                                                                                                                                                                                                             'na '
                                                                                                                                                                                                                                                             'mapitio '
                                                                                                                                                                                                                                                             'yanabaki '
                                                                                                                                                                                                                                                             'yamehifadhiwa. '
                                                                                                                                                                                                                                                             'Msimamizi '
                                                                                                                                                                                                                                                             'mwenye '
                                                                                                                                                                                                                                                             'akaunti '
                                                                                                                                                                                                                                                             'inayotumika '
                                                                                                                                                                                                                                                             'katika '
                                                                                                                                                                                                                                                             'kituo '
                                                                                                                                                                                                                                                             'chako '
                                                                                                                                                                                                                                                             'anaweza '
                                                                                                                                                                                                                                                             'kuwezesha '
                                                                                                                                                                                                                                                             'akaunti '
                                                                                                                                                                                                                                                             'tena. '
                                                                                                                                                                                                                                                             'Msimamizi '
                                                                                                                                                                                                                                                             'wa '
                                                                                                                                                                                                                                                             'mwisho '
                                                                                                                                                                                                                                                             'mwenye '
                                                                                                                                                                                                                                                             'akaunti '
                                                                                                                                                                                                                                                             'inayotumika '
                                                                                                                                                                                                                                                             'hawezi '
                                                                                                                                                                                                                                                             'kujizimia '
                                                                                                                                                                                                                                                             'akaunti.',
 'Create and view reviews': 'Unda na uone mapitio',
 'Open Analyse Image, upload a supported de-identified image and save the preview. History contains only your own reviews and supports CSV export. Model integration is pending; awaiting-model records are not predictions.': 'Fungua '
                                                                                                                                                                                                                               'Changanua '
                                                                                                                                                                                                                               'Picha, '
                                                                                                                                                                                                                               'pakia '
                                                                                                                                                                                                                               'picha '
                                                                                                                                                                                                                               'inayokubalika '
                                                                                                                                                                                                                               'isiyo '
                                                                                                                                                                                                                               'na '
                                                                                                                                                                                                                               'taarifa '
                                                                                                                                                                                                                               'za '
                                                                                                                                                                                                                               'utambulisho '
                                                                                                                                                                                                                               'na '
                                                                                                                                                                                                                               'uhifadhi '
                                                                                                                                                                                                                               'picha '
                                                                                                                                                                                                                               'ndogo. '
                                                                                                                                                                                                                               'Historia '
                                                                                                                                                                                                                               'ina '
                                                                                                                                                                                                                               'mapitio '
                                                                                                                                                                                                                               'yako '
                                                                                                                                                                                                                               'pekee '
                                                                                                                                                                                                                               'na '
                                                                                                                                                                                                                               'inaweza '
                                                                                                                                                                                                                               'kupakuliwa '
                                                                                                                                                                                                                               'kama '
                                                                                                                                                                                                                               'CSV. '
                                                                                                                                                                                                                               'Modeli '
                                                                                                                                                                                                                               'bado '
                                                                                                                                                                                                                               'haijaunganishwa; '
                                                                                                                                                                                                                               'rekodi '
                                                                                                                                                                                                                               'zinazosubiri '
                                                                                                                                                                                                                               'modeli '
                                                                                                                                                                                                                               'si '
                                                                                                                                                                                                                               'matokeo '
                                                                                                                                                                                                                               'ya '
                                                                                                                                                                                                                               'modeli.',
 'Update or delete a review': 'Sasisha au futa mapitio',
 'Open Review Records to update a case reference or permanently delete one of your own reviews. Deletion cannot be undone.': 'Fungua '
                                                                                                                             'Rekodi '
                                                                                                                             'za '
                                                                                                                             'Mapitio '
                                                                                                                             'kusasisha '
                                                                                                                             'rejea '
                                                                                                                             'ya '
                                                                                                                             'kisa '
                                                                                                                             'au '
                                                                                                                             'kufuta '
                                                                                                                             'kabisa '
                                                                                                                             'mapitio '
                                                                                                                             'yako. '
                                                                                                                             'Ufutaji '
                                                                                                                             'hauwezi '
                                                                                                                             'kutenduliwa.',
 'Administrator tasks': 'Kazi za msimamizi',
 'User Management controls account access within your centre. Dataset Status manages imported dataset metadata. Database Guide explains the tables and CRUD actions and shows database health.': 'Usimamizi '
                                                                                                                                                                                                 'wa '
                                                                                                                                                                                                 'Watumiaji '
                                                                                                                                                                                                 'hudhibiti '
                                                                                                                                                                                                 'matumizi '
                                                                                                                                                                                                 'ya '
                                                                                                                                                                                                 'akaunti '
                                                                                                                                                                                                 'katika '
                                                                                                                                                                                                 'kituo '
                                                                                                                                                                                                 'chako. '
                                                                                                                                                                                                 'Hali '
                                                                                                                                                                                                 'ya '
                                                                                                                                                                                                 'Seti '
                                                                                                                                                                                                 'za '
                                                                                                                                                                                                 'Data '
                                                                                                                                                                                                 'husimamia '
                                                                                                                                                                                                 'taarifa '
                                                                                                                                                                                                 'za '
                                                                                                                                                                                                 'data '
                                                                                                                                                                                                 'zilizoingizwa. '
                                                                                                                                                                                                 'Mwongozo '
                                                                                                                                                                                                 'wa '
                                                                                                                                                                                                 'Hifadhidata '
                                                                                                                                                                                                 'hufafanua '
                                                                                                                                                                                                 'majedwali '
                                                                                                                                                                                                 'na '
                                                                                                                                                                                                 'hatua '
                                                                                                                                                                                                 'za '
                                                                                                                                                                                                 'CRUD '
                                                                                                                                                                                                 'na '
                                                                                                                                                                                                 'kuonyesha '
                                                                                                                                                                                                 'hali '
                                                                                                                                                                                                 'ya '
                                                                                                                                                                                                 'hifadhidata.',
 'Image reviews': 'Mapitio ya picha',
 "Sign out and use your separate Healthcare Worker account to upload images or access review history. Administrator access does not expose other users' private reviews. Previously saved administrator reviews remain retained in the database.": 'Ondoka '
                                                                                                                                                                                                                                                   'na '
                                                                                                                                                                                                                                                   'utumie '
                                                                                                                                                                                                                                                   'akaunti '
                                                                                                                                                                                                                                                   'yako '
                                                                                                                                                                                                                                                   'tofauti '
                                                                                                                                                                                                                                                   'ya '
                                                                                                                                                                                                                                                   'Mhudumu '
                                                                                                                                                                                                                                                   'wa '
                                                                                                                                                                                                                                                   'Afya '
                                                                                                                                                                                                                                                   'kupakia '
                                                                                                                                                                                                                                                   'picha '
                                                                                                                                                                                                                                                   'au '
                                                                                                                                                                                                                                                   'kuona '
                                                                                                                                                                                                                                                   'historia '
                                                                                                                                                                                                                                                   'ya '
                                                                                                                                                                                                                                                   'mapitio. '
                                                                                                                                                                                                                                                   'Akaunti '
                                                                                                                                                                                                                                                   'ya '
                                                                                                                                                                                                                                                   'msimamizi '
                                                                                                                                                                                                                                                   'haionyeshi '
                                                                                                                                                                                                                                                   'mapitio '
                                                                                                                                                                                                                                                   'binafsi '
                                                                                                                                                                                                                                                   'ya '
                                                                                                                                                                                                                                                   'wengine. '
                                                                                                                                                                                                                                                   'Mapitio '
                                                                                                                                                                                                                                                   'ya '
                                                                                                                                                                                                                                                   'msimamizi '
                                                                                                                                                                                                                                                   'yaliyohifadhiwa '
                                                                                                                                                                                                                                                   'awali '
                                                                                                                                                                                                                                                   'yanabaki '
                                                                                                                                                                                                                                                   'katika '
                                                                                                                                                                                                                                                   'hifadhidata.',
 'Only active System Administrators can manage accounts.': 'Ni Wasimamizi wa Mfumo wenye akaunti '
                                                           'zinazotumika pekee wanaoweza kusimamia '
                                                           'akaunti.',
 'Manage access within your centre. Suspending or deactivating an account retains its saved records.': 'Simamia '
                                                                                                       'matumizi '
                                                                                                       'ya '
                                                                                                       'akaunti '
                                                                                                       'katika '
                                                                                                       'kituo '
                                                                                                       'chako. '
                                                                                                       'Kusimamisha '
                                                                                                       'au '
                                                                                                       'kuzima '
                                                                                                       'akaunti '
                                                                                                       'hakufuti '
                                                                                                       'rekodi '
                                                                                                       'zake.',
 'Password hashes and session tokens are not displayed. Centre names remain self-declared.': 'Alama '
                                                                                             'za '
                                                                                             'nenosiri '
                                                                                             'na '
                                                                                             'tokeni '
                                                                                             'za '
                                                                                             'vipindi '
                                                                                             'hazionyeshwi. '
                                                                                             'Majina '
                                                                                             'ya '
                                                                                             'vituo '
                                                                                             'hutolewa '
                                                                                             'na '
                                                                                             'watumiaji '
                                                                                             'wenyewe.',
 'No other accounts to manage.': 'Hakuna akaunti nyingine za kusimamia.',
 'Select an account': 'Chagua akaunti',
 'Current status:': 'Hali ya sasa:',
 'Suspend prevents access. Restore/reactivate permits sign-in again. Saved reviews are retained.': 'Kusimamisha '
                                                                                                   'kunazuia '
                                                                                                   'matumizi '
                                                                                                   'ya '
                                                                                                   'akaunti. '
                                                                                                   'Kurejesha '
                                                                                                   'au '
                                                                                                   'kuwezesha '
                                                                                                   'tena '
                                                                                                   'kunaruhusu '
                                                                                                   'kuingia. '
                                                                                                   'Mapitio '
                                                                                                   'yaliyohifadhiwa '
                                                                                                   'yanabaki.',
 'I confirm this account action is authorised.': 'Nathibitisha kuwa hatua hii ya akaunti '
                                                 'imeruhusiwa.',
 'Suspend account': 'Simamisha akaunti',
 'Restore / reactivate account': 'Rejesha / wezesha akaunti tena',
 'Confirm the account action first.': 'Thibitisha hatua ya akaunti kwanza.',
 'Account suspended.': 'Akaunti imesimamishwa.',
 'Account restored. The user can sign in again.': 'Akaunti imerejeshwa. Mtumiaji anaweza kuingia '
                                                  'tena.',
 'Create in Analyse Image, read your saved records here, update a case reference or delete a review.': 'Unda '
                                                                                                       'mapitio '
                                                                                                       'katika '
                                                                                                       'Changanua '
                                                                                                       'Picha, '
                                                                                                       'soma '
                                                                                                       'rekodi '
                                                                                                       'zako '
                                                                                                       'hapa, '
                                                                                                       'sasisha '
                                                                                                       'rejea '
                                                                                                       'ya '
                                                                                                       'kisa '
                                                                                                       'au '
                                                                                                       'futa '
                                                                                                       'mapitio.',
 'Create a new review': 'Unda mapitio mapya',
 'Select your review': 'Chagua mapitio yako',
 'Update case reference': 'Sasisha rejea ya kisa',
 'Case reference updated.': 'Rejea ya kisa imesasishwa.',
 'Deleting a review permanently removes its thumbnail and related prediction records. Your account remains saved.': 'Kufuta '
                                                                                                                    'mapitio '
                                                                                                                    'huondoa '
                                                                                                                    'kabisa '
                                                                                                                    'picha '
                                                                                                                    'ndogo '
                                                                                                                    'na '
                                                                                                                    'rekodi '
                                                                                                                    'za '
                                                                                                                    'matokeo '
                                                                                                                    'zinazohusiana. '
                                                                                                                    'Akaunti '
                                                                                                                    'yako '
                                                                                                                    'inabaki '
                                                                                                                    'imehifadhiwa.',
 'Permanently delete this review.': 'Futa kabisa mapitio haya.',
 'Confirm deletion first.': 'Thibitisha ufutaji kwanza.',
 'Review unavailable.': 'Mapitio hayapatikani.',
 'Only active administrators can view database health.': 'Ni wasimamizi wenye akaunti zinazotumika '
                                                         'pekee wanaoweza kuona hali ya '
                                                         'hifadhidata.',
 'The app database stores accounts, sessions, saved reviews and imported dataset metadata. The Colab training database is a separate file.': 'Hifadhidata '
                                                                                                                                             'ya '
                                                                                                                                             'programu '
                                                                                                                                             'huhifadhi '
                                                                                                                                             'akaunti, '
                                                                                                                                             'vipindi, '
                                                                                                                                             'mapitio '
                                                                                                                                             'na '
                                                                                                                                             'taarifa '
                                                                                                                                             'za '
                                                                                                                                             'seti '
                                                                                                                                             'za '
                                                                                                                                             'data '
                                                                                                                                             'zilizoingizwa. '
                                                                                                                                             'Hifadhidata '
                                                                                                                                             'ya '
                                                                                                                                             'mafunzo '
                                                                                                                                             'ya '
                                                                                                                                             'Colab '
                                                                                                                                             'ni '
                                                                                                                                             'faili '
                                                                                                                                             'tofauti.',
 'Create, Read, Update, Delete': 'Unda, Soma, Sasisha, Futa',
 'Action': 'Hatua',
 'Meaning': 'Maana',
 'In the app': 'Katika programu',
 'Create': 'Unda',
 'Read': 'Soma',
 'Update': 'Sasisha',
 'Delete': 'Futa',
 'Add a record': 'Ongeza rekodi',
 'View saved records': 'Angalia rekodi zilizohifadhiwa',
 'Change a record': 'Badilisha rekodi',
 'Permanently remove a record': 'Ondoa rekodi kabisa',
 'Register an account or save an image review': 'Sajili akaunti au hifadhi mapitio ya picha',
 'Open your history or view account details': 'Fungua historia yako au angalia taarifa za akaunti',
 'Edit your profile, change a case reference, deactivate or restore access': 'Hariri wasifu, '
                                                                             'badilisha rejea ya '
                                                                             'kisa, zima au '
                                                                             'rejesha matumizi ya '
                                                                             'akaunti',
 'Delete your own review and its related prediction records': 'Futa mapitio yako na rekodi zake za '
                                                              'matokeo',
 'Deactivation is Update, not Delete. The account and its reviews remain saved.': 'Kuzima akaunti '
                                                                                  'ni Kusasisha, '
                                                                                  'si Kufuta. '
                                                                                  'Akaunti na '
                                                                                  'mapitio yake '
                                                                                  'hubaki '
                                                                                  'yamehifadhiwa.',
 'What the tables mean': 'Maana ya majedwali',
 'Purpose': 'Matumizi',
 'Profiles, roles, account status and salted password hashes': 'Wasifu, majukumu, hali za akaunti '
                                                               'na alama za nenosiri zenye thamani '
                                                               'nasibu ya ziada',
 'Hashed sign-in tokens and expiry times': 'Alama za tokeni za kuingia na muda wake wa kuisha',
 'Failed sign-in counts and temporary lockouts': 'Idadi ya majaribio ya kuingia yaliyoshindwa na '
                                                 'vizuizi vya muda',
 'Review ownership, filenames, case references and thumbnails': 'Wamiliki wa mapitio, majina ya '
                                                                'faili, rejea za visa na picha '
                                                                'ndogo',
 'Review status and model results when integrated': 'Hali ya mapitio na matokeo ya modeli '
                                                    'itakapounganishwa',
 'Model descriptions and supported classes': 'Maelezo ya modeli na aina zinazotumika',
 'Imported clean metadata and import history': 'Taarifa safi za data zilizoingizwa na historia ya '
                                               'uingizaji',
 'Timestamped account and review actions': 'Hatua za akaunti na mapitio zenye tarehe na saa',
 'Database migration versions': 'Matoleo ya mabadiliko ya muundo wa hifadhidata',
 'Legacy invitation records, if present, are retained for history and are no longer used. Current account approval fields have been removed.': 'Rekodi '
                                                                                                                                               'za '
                                                                                                                                               'zamani '
                                                                                                                                               'za '
                                                                                                                                               'mialiko, '
                                                                                                                                               'zikiwepo, '
                                                                                                                                               'hubaki '
                                                                                                                                               'kwa '
                                                                                                                                               'historia '
                                                                                                                                               'lakini '
                                                                                                                                               'hazitumiki '
                                                                                                                                               'tena. '
                                                                                                                                               'Sehemu '
                                                                                                                                               'za '
                                                                                                                                               'idhini '
                                                                                                                                               'ya '
                                                                                                                                               'akaunti '
                                                                                                                                               'zimeondolewa.',
 'Current database checks': 'Ukaguzi wa sasa wa hifadhidata',
 'Integrity:': 'Uadilifu:',
 'Relationship errors:': 'Hitilafu za uhusiano wa rekodi:',
 'Foreign keys enabled:': 'Uhusiano wa rekodi umewezeshwa:',
 'Saved rows': 'Rekodi zilizohifadhiwa',
 "No password hashes, session tokens or other users' review content are displayed here.": 'Alama '
                                                                                          'za '
                                                                                          'nenosiri, '
                                                                                          'tokeni '
                                                                                          'za '
                                                                                          'vipindi '
                                                                                          'na '
                                                                                          'maudhui '
                                                                                          'ya '
                                                                                          'mapitio '
                                                                                          'ya '
                                                                                          'watumiaji '
                                                                                          'wengine '
                                                                                          'havionyeshwi '
                                                                                          'hapa.',
 'Research decision-support prototype. It does not provide a medical diagnosis. Suspected skin cancer requires assessment by a qualified healthcare professional.': 'Mfumo '
                                                                                                                                                                    'wa '
                                                                                                                                                                    'majaribio '
                                                                                                                                                                    'wa '
                                                                                                                                                                    'kusaidia '
                                                                                                                                                                    'maamuzi '
                                                                                                                                                                    'katika '
                                                                                                                                                                    'utafiti. '
                                                                                                                                                                    'Hautoi '
                                                                                                                                                                    'utambuzi '
                                                                                                                                                                    'wa '
                                                                                                                                                                    'kitabibu. '
                                                                                                                                                                    'Shaka '
                                                                                                                                                                    'ya '
                                                                                                                                                                    'saratani '
                                                                                                                                                                    'ya '
                                                                                                                                                                    'ngozi '
                                                                                                                                                                    'inahitaji '
                                                                                                                                                                    'tathmini '
                                                                                                                                                                    'ya '
                                                                                                                                                                    'mtaalamu '
                                                                                                                                                                    'wa '
                                                                                                                                                                    'afya '
                                                                                                                                                                    'mwenye '
                                                                                                                                                                    'sifa.',
 'Your session has ended or your account is inactive. Please sign in again.': 'Kipindi chako '
                                                                              'kimeisha au akaunti '
                                                                              'yako haitumiki. '
                                                                              'Tafadhali ingia '
                                                                              'tena.',
 'Your session has ended. Sign in again.': 'Kipindi chako kimeisha. Ingia tena.',
 'This account role is not supported.': 'Aina hii ya akaunti haitumiki.',
 'Use your separate Healthcare Worker account for image reviews.': 'Tumia akaunti yako tofauti ya '
                                                                   'Mhudumu wa Afya kwa mapitio ya '
                                                                   'picha.',
 'This page is available only to active System Administrators.': 'Ukurasa huu ni wa Wasimamizi wa '
                                                                 'Mfumo wenye akaunti zinazotumika '
                                                                 'pekee.',
 'Return to dashboard': 'Rudi kwenye dashibodi',
 'Enter a valid email address.': 'Weka anwani halali ya barua pepe.',
 'Enter a name with 2–100 characters.': 'Weka jina lenye herufi 2–100.',
 'Enter a healthcare centre name with 2–150 characters.': 'Weka jina la kituo cha afya lenye '
                                                          'herufi 2–150.',
 'This account is not active. Contact your healthcare centre administrator.': 'Akaunti hii '
                                                                              'haitumiki. '
                                                                              'Wasiliana na '
                                                                              'msimamizi wa kituo '
                                                                              'chako cha afya.',
 'Your administrator and healthcare-worker accounts must use different passwords.': 'Akaunti zako '
                                                                                    'za msimamizi '
                                                                                    'na mhudumu wa '
                                                                                    'afya lazima '
                                                                                    'zitumie '
                                                                                    'manenosiri '
                                                                                    'tofauti.',
 'Choose System Administrator or Healthcare Worker.': 'Chagua Msimamizi wa Mfumo au Mhudumu wa '
                                                      'Afya.',
 'Use only one set of linked-account credentials.': 'Tumia taarifa za kuingia za akaunti moja '
                                                    'iliyopo pekee.',
 'Enter both the existing account email and its current password.': 'Weka barua pepe na nenosiri '
                                                                    'la sasa la akaunti iliyopo.',
 'Link your existing account for the other role.': 'Unganisha akaunti yako iliyopo ya jukumu '
                                                   'jingine.',
 'Administrator credentials can link a new healthcare-worker account only.': 'Taarifa za msimamizi '
                                                                             'zinaweza kuunganisha '
                                                                             'akaunti mpya ya '
                                                                             'mhudumu wa afya '
                                                                             'pekee.',
 'Enter both the administrator email and its current password to link your accounts.': 'Weka barua '
                                                                                       'pepe na '
                                                                                       'nenosiri '
                                                                                       'la sasa la '
                                                                                       'msimamizi '
                                                                                       'ili '
                                                                                       'kuunganisha '
                                                                                       'akaunti '
                                                                                       'zako.',
 'The linked account must be your system-administrator account.': 'Akaunti inayounganishwa lazima '
                                                                  'iwe akaunti yako ya msimamizi '
                                                                  'wa mfumo.',
 'Use an existing account for the other role.': 'Tumia akaunti iliyopo ya jukumu jingine.',
 'Use a different email for your second-role account.': 'Tumia barua pepe tofauti kwa akaunti ya '
                                                        'jukumu la pili.',
 'Registration could not be completed. Try signing in or use another email.': 'Usajili '
                                                                              'haukukamilika. '
                                                                              'Jaribu kuingia au '
                                                                              'tumia barua pepe '
                                                                              'nyingine.',
 'Email or password is incorrect.': 'Barua pepe au nenosiri si sahihi.',
 'Too many failed attempts. Try again in 15 minutes.': 'Majaribio mengi yameshindwa. Jaribu tena '
                                                       'baada ya dakika 15.',
 'This legacy account is inactive. Contact your healthcare centre administrator.': 'Akaunti hii ya '
                                                                                   'zamani '
                                                                                   'haitumiki. '
                                                                                   'Wasiliana na '
                                                                                   'msimamizi wa '
                                                                                   'kituo chako '
                                                                                   'cha afya.',
 'Your account is suspended. Contact your centre administrator.': 'Akaunti yako imesimamishwa. '
                                                                  'Wasiliana na msimamizi wa kituo '
                                                                  'chako.',
 'Your profile is deactivated. Contact your centre administrator to reactivate it.': 'Wasifu wako '
                                                                                     'umezimwa. '
                                                                                     'Wasiliana na '
                                                                                     'msimamizi wa '
                                                                                     'kituo chako '
                                                                                     'ili '
                                                                                     'kuuwezesha '
                                                                                     'tena.',
 'The current password is incorrect.': 'Nenosiri la sasa si sahihi.',
 'Choose a password different from the current password.': 'Chagua nenosiri tofauti na la sasa.',
 'Account unavailable.': 'Akaunti haipatikani.',
 'An administrator centre change requires host-level authorisation. Your centre cannot be changed here.': 'Kubadilisha '
                                                                                                          'kituo '
                                                                                                          'cha '
                                                                                                          'msimamizi '
                                                                                                          'kunahitaji '
                                                                                                          'ruhusa '
                                                                                                          'ya '
                                                                                                          'mwenyeji '
                                                                                                          'wa '
                                                                                                          'mfumo. '
                                                                                                          'Huwezi '
                                                                                                          'kubadilisha '
                                                                                                          'kituo '
                                                                                                          'chako '
                                                                                                          'hapa.',
 'Record unavailable.': 'Rekodi haipatikani.',
 'Only active System Administrators can perform this action.': 'Ni Wasimamizi wa Mfumo wenye '
                                                               'akaunti zinazotumika pekee '
                                                               'wanaoweza kufanya hatua hii.',
 'Complete your healthcare centre profile first.': 'Kamilisha taarifa za kituo chako cha afya '
                                                   'kwanza.',
 'Choose restore or suspend.': 'Chagua kurejesha au kusimamisha.',
 'Manage accounts only within your healthcare centre.': 'Simamia akaunti za kituo chako cha afya '
                                                        'pekee.',
 'Use Account settings to deactivate your own profile.': 'Tumia mipangilio ya Akaunti kuzima '
                                                         'wasifu wako.',
 'This account already has that status.': 'Akaunti hii tayari ina hali hiyo.',
 'Only an active account can be suspended.': 'Ni akaunti inayotumika pekee inayoweza kusimamishwa.',
 'Sign in again before deactivating your profile.': 'Ingia tena kabla ya kuzima wasifu wako.',
 'Another active administrator at your healthcare centre is required before you can deactivate your profile.': 'Lazima '
                                                                                                               'kuwe '
                                                                                                               'na '
                                                                                                               'msimamizi '
                                                                                                               'mwingine '
                                                                                                               'mwenye '
                                                                                                               'akaunti '
                                                                                                               'inayotumika '
                                                                                                               'katika '
                                                                                                               'kituo '
                                                                                                               'chako '
                                                                                                               'kabla '
                                                                                                               'ya '
                                                                                                               'kuzima '
                                                                                                               'wasifu '
                                                                                                               'wako.',
 'Case reference must be at most 80 characters.': 'Rejea ya kisa isizidi herufi 80.',
 'Manifest must be smaller than 20 MB.': 'Orodha ya data lazima iwe chini ya MB 20.',
 'The manifest contains no records.': 'Orodha ya data haina rekodi.',
 'Image reviews are available only through a Healthcare Worker account. Sign in with your separate Healthcare Worker credentials.': 'Mapitio '
                                                                                                                                    'ya '
                                                                                                                                    'picha '
                                                                                                                                    'yanapatikana '
                                                                                                                                    'kupitia '
                                                                                                                                    'akaunti '
                                                                                                                                    'ya '
                                                                                                                                    'Mhudumu '
                                                                                                                                    'wa '
                                                                                                                                    'Afya '
                                                                                                                                    'pekee. '
                                                                                                                                    'Ingia '
                                                                                                                                    'kwa '
                                                                                                                                    'taarifa '
                                                                                                                                    'zako '
                                                                                                                                    'tofauti '
                                                                                                                                    'za '
                                                                                                                                    'Mhudumu '
                                                                                                                                    'wa '
                                                                                                                                    'Afya.',
 'Choose a genuine JPG or PNG image.': 'Chagua picha halisi ya JPG au PNG.',
 'Choose a nonempty image smaller than 10 MB.': 'Chagua picha yenye maudhui na ukubwa chini ya MB '
                                                '10.',
 'Choose a still image rather than an animation.': 'Chagua picha tuli badala ya picha inayosogea.',
 'Use an image with no more than 20 million pixels.': 'Tumia picha isiyozidi pikseli milioni 20.',
 'The image could not be read. Choose another JPG or PNG.': 'Picha haikuweza kusomwa. Chagua JPG '
                                                            'au PNG nyingine.',
 'Unexpected user columns; migration stopped to protect data.': 'Sehemu za watumiaji '
                                                                'zisizotarajiwa zimepatikana; '
                                                                'mabadiliko yamesimamishwa kulinda '
                                                                'data.',
 'Migration relationship checks failed; changes rolled back.': 'Ukaguzi wa uhusiano wa rekodi '
                                                               'wakati wa mabadiliko umeshindwa; '
                                                               'mabadiliko yametenduliwa.',
 'A custom index/trigger uses approval fields; inspect it before migrating.': 'Faharasa au '
                                                                              'kichochezi maalumu '
                                                                              'kinatumia sehemu za '
                                                                              'idhini; kikague '
                                                                              'kabla ya '
                                                                              'kubadilisha '
                                                                              'hifadhidata.',
 'dataset': 'Seti ya data',
 'class_label': 'Aina',
 'image_count': 'Idadi ya picha',
 'True': 'Ndiyo',
 'False': 'Hapana',
 'ok': 'Sawa',
 '**Dashboard** — account role, healthcare centre and activity': '**Dashibodi** — aina ya akaunti, '
                                                                 'kituo cha afya na shughuli',
 '**Analyse Image** — upload, preview and save a review': '**Changanua Picha** — pakia, angalia na '
                                                          'uhifadhi mapitio',
 '**History** — saved records and CSV export': '**Historia** — rekodi zilizohifadhiwa na upakuaji '
                                               'wa CSV',
 '**Account** — profile and password settings': '**Akaunti** — mipangilio ya wasifu na nenosiri',
 '**User Management** — administrator account controls': '**Usimamizi wa Watumiaji** — udhibiti wa '
                                                         'akaunti za watumiaji',
 '**Help** — instructions and project scope': '**Msaada** — maelekezo ya kutumia programu',
 '**Help** — instructions for using the app': '**Msaada** — maelekezo ya kutumia programu',
 '**Review Records** — update case references and delete your own reviews': '**Rekodi za Mapitio** '
                                                                            '— sasisha rejea za '
                                                                            'visa na ufute mapitio '
                                                                            'yako'}

PATTERNS = [
    (r"Imported ([\d,]+) verified metadata rows\. Refresh this page to see the updated totals\.",
     "Rekodi za taarifa zilizothibitishwa {0} zimeingizwa. Onyesha ukurasa upya kuona jumla mpya."),
    (r"(Healthcare Worker|System Administrator) account created\. Use the Sign in tab to continue\.",
     "Akaunti ya {0} imefunguliwa. Tumia kichupo cha Ingia kuendelea."),
    (r"(Active|Suspended|Deactivated) accounts", "Akaunti: {0}"),
    (r"Review #(\d+)", "Mapitio #{0}"),
    (r"Invalid required metadata in CSV row (\d+)\.", "Taarifa zinazohitajika si sahihi katika mstari wa CSV {0}."),
    (r"Duplicate identifier or image hash in CSV row (\d+)\.", "Kitambulisho au alama ya picha imerudiwa katika mstari wa CSV {0}."),
    (r"Invalid age in CSV row (\d+)\.", "Umri si sahihi katika mstari wa CSV {0}."),
    (r"Invalid sex label in CSV row (\d+)\.", "Taarifa ya jinsia si sahihi katika mstari wa CSV {0}."),
    (r"Invalid Fitzpatrick category in CSV row (\d+)\.", "Kundi la Fitzpatrick si sahihi katika mstari wa CSV {0}."),
    (r"Invalid biopsy flag in CSV row (\d+)\.", "Taarifa ya biopsy si sahihi katika mstari wa CSV {0}."),
    (r"(\d+) × (\d+) pixels · ([\d.]+) KB", "Pikseli {0} × {1} · KB {2}"),
]

def current_language():
    """Read a non-widget preference that survives page changes."""
    if st.session_state.get("app_language") not in {"en", "sw"}:
        previous = st.session_state.get("language", "en")
        st.session_state["app_language"] = previous if previous in {"en", "sw"} else "en"
    return st.session_state["app_language"]


def _save_language():
    selected = st.session_state.get("_language_choice", "en")
    st.session_state["app_language"] = selected if selected in {"en", "sw"} else "en"


def language_selector():
    # The widget may be cleared on navigation; the preference is not a widget.
    st.session_state["_language_choice"] = current_language()
    st.sidebar.selectbox(
        "Language / Lugha",
        options=["en", "sw"],
        format_func=lambda code: "English" if code == "en" else "Kiswahili",
        key="_language_choice",
        on_change=_save_language,
    )


def t(value):
    if not isinstance(value, str) or current_language() != "sw":
        return value
    if value in CATALOG:
        return CATALOG[value]
    # Translate labels joined with dynamic values without translating their contents.
    for prefix, translated in [
        ("Welcome back, ", "Karibu tena, "),
        ("Registered ", "Tarehe ya usajili "),
        ("**Account role:** ", "**Aina ya akaunti:** "),
        ("**Healthcare centre:** ", "**Kituo cha afya:** "),
        ("Use the clean_metadata.csv exported by notebook 3. Required columns: ",
         "Tumia clean_metadata.csv iliyotolewa na daftari la 3. Sehemu zinazohitajika: "),
    ]:
        if value.startswith(prefix):
            suffix = value[len(prefix):]
            if prefix == "**Account role:** ":
                suffix = CATALOG.get(suffix, suffix)
            return translated + suffix
    for pattern, template in PATTERNS:
        match = re.fullmatch(pattern, value)
        if match:
            return template.format(*[CATALOG.get(x, x) for x in match.groups()])
    if "\n" in value:
        return "\n".join(t(line.strip()) for line in value.split("\n"))
    # Unexpected technical errors remain visible rather than being misrepresented.
    return value

def display_data(value):
    """Localize table headings and controlled display values, never user-entered fields."""
    controlled = {"Role", "Status", "Action", "Meaning", "In the app", "Purpose"}
    if isinstance(value, list):
        if all(isinstance(row, dict) for row in value):
            return [{t(key): t(item) if key in controlled else item
                     for key, item in row.items()} for row in value]
        return [t(item) for item in value]
    # Pandas is already used by Streamlit; avoid adding a new dependency here.
    if hasattr(value, "columns") and hasattr(value, "rename"):
        result = value.copy()
        for column in controlled.intersection(result.columns):
            result[column] = result[column].map(t)
        return result.rename(columns=lambda column: t(column))
    return value

def translated_format(formatter):
    return lambda value: t(formatter(value))