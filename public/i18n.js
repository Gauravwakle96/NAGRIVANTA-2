'use strict';

(() => {
  const dictionaries = {
    mr: {
      "Language":"भाषा","WELCOME TO NAGRIVANTA":"नग्रिवंतामध्ये स्वागत","Sign in to your workspace":"तुमच्या कार्यक्षेत्रात साइन इन करा",
      "Use your account to access the right civic workflow.":"योग्य नागरी कार्यप्रवाह वापरण्यासाठी तुमच्या खात्यात प्रवेश करा.",
      "Explore Live Demo":"थेट डेमो पाहा","Register as Citizen":"नागरिक म्हणून नोंदणी करा","Sign In":"साइन इन",
      "Create citizen account":"नागरिक खाते तयार करा","Email address":"ईमेल पत्ता","Password":"पासवर्ड",
      "Your name":"तुमचे नाव","Create citizen account →":"नागरिक खाते तयार करा →",
      "Your account is role-restricted.":"तुमच्या खात्याला भूमिका-आधारित मर्यादा आहेत.",
      "Evidence is private to authorized participants in a complaint.":"पुरावे फक्त तक्रारीतील अधिकृत सहभागींसाठी उपलब्ध आहेत.",
      "INTERACTIVE DEMO — Uses synthetic demonstration data.":"परस्परसंवादी डेमो — कृत्रिम प्रात्यक्षिक माहिती वापरली आहे.",
      "Explore Nagrivanta":"नग्रिवंता पाहा","Start Guided Tour":"मार्गदर्शित फेरफटका सुरू करा","Explore Freely":"स्वतंत्रपणे पाहा",
      "Back to sign in":"साइन इनकडे परत जा","Citizen":"नागरिक","Municipal Administrator":"महानगरपालिका प्रशासक",
      "Municipal administrator":"महानगरपालिका प्रशासक","Field Worker":"क्षेत्र कर्मचारी","Field worker":"क्षेत्र कर्मचारी",
      "Inspector":"निरीक्षक","System Administrator":"प्रणाली प्रशासक","System administrator":"प्रणाली प्रशासक",
      "Open Citizen portal":"नागरिक पोर्टल उघडा","Open Municipal portal":"महानगरपालिका पोर्टल उघडा",
      "Open Field Worker portal":"क्षेत्र कर्मचारी पोर्टल उघडा","Open Inspector portal":"निरीक्षक पोर्टल उघडा",
      "Open System Admin portal":"प्रणाली प्रशासक पोर्टल उघडा","Reset demo":"डेमो रीसेट करा","Exit demo":"डेमोमधून बाहेर पडा",
      "My complaints":"माझ्या तक्रारी","Report an issue":"समस्या नोंदवा","Heritage watch":"वारसा निरीक्षण",
      "Notifications":"सूचना","Operations":"कामकाज","Analytics":"विश्लेषण","My work queue":"माझी कामांची यादी",
      "Inspection queue":"तपासणी यादी","Administration":"प्रशासन","Change password":"पासवर्ड बदला",
      "Sign out":"साइन आउट","Your civic reports":"तुमच्या नागरी तक्रारी","Track updates from submission through field work and inspection.":"तक्रार नोंदणीपासून क्षेत्रीय काम आणि तपासणीपर्यंतचे बदल पाहा.",
      "Complaint history":"तक्रार इतिहास","Your submissions only":"फक्त तुमच्या नोंदी","All statuses":"सर्व स्थिती",
      "Submitted":"नोंदवले","Assigned":"नियुक्त","Work in progress":"काम सुरू आहे","Awaiting inspection":"तपासणी प्रलंबित",
      "Rework required":"पुन्हा काम आवश्यक","Resolved":"निराकरण झाले","No complaints yet":"अद्याप तक्रारी नाहीत",
      "Submit a civic issue to begin tracking the response.":"प्रतिसादाचा मागोवा घेण्यासाठी नागरी समस्या नोंदवा.",
      "Report a civic issue":"नागरी समस्या नोंदवा","Share a clear location and supporting evidence. Recommendations are reviewed by municipal staff.":"स्पष्ट ठिकाण आणि पूरक पुरावे द्या. शिफारसींचे महानगरपालिका कर्मचारी पुनरावलोकन करतात.",
      "Issue category and subcategory":"समस्येचा प्रकार आणि उपप्रकार","Short title":"संक्षिप्त शीर्षक",
      "Ward or locality":"प्रभाग किंवा परिसर","Specific location":"अचूक ठिकाण","What is happening?":"काय घडत आहे?",
      "Photo evidence":"छायाचित्र पुरावा","Submit complaint":"तक्रार सादर करा","Submitting…":"सादर करत आहे…",
      "How do I submit a complaint?":"तक्रार कशी सादर करावी?","How do I track a complaint?":"तक्रारीचा मागोवा कसा घ्यावा?",
      "What do statuses mean?":"स्थितींचा अर्थ काय?","How do assignment and inspection work?":"नियुक्ती आणि तपासणी कशी चालते?",
      "What happens after rework is requested?":"पुन्हा काम मागितल्यावर काय होते?","How does the demo work?":"डेमो कसा वापरावा?",
      "Could not load this view":"हे दृश्य लोड करता आले नाही","Try again":"पुन्हा प्रयत्न करा",
      "Feedback":"अभिप्राय","Submit feedback":"अभिप्राय सादर करा","Rating":"रेटिंग",
      "No new update is available yet.":"अद्याप नवीन अद्यतन उपलब्ध नाही.",
      "A similar unresolved report may already exist.":"यासारखी न सुटलेली तक्रार आधीपासून असू शकते.",
      "Thank you. Your feedback was recorded.":"धन्यवाद. तुमचा अभिप्राय नोंदवला आहे.",
      "See how a public issue can move through citizen reporting, municipal review, field work, inspection, and resolution. This is an isolated demo, not live government activity.":"नागरिक अहवाल, महानगरपालिका पुनरावलोकन, क्षेत्रीय काम, तपासणी आणि निराकरणाचा प्रवास पाहा. हा वेगळा डेमो आहे; सरकारी कामकाज नाही.",
      "Submit and track an issue; receive updates and rate a verified resolution.":"समस्या नोंदवा, मागोवा घ्या, अद्यतने मिळवा आणि प्रमाणित निराकरणाला रेटिंग द्या.",
      "Review reports, routing suggestions, and assign a field worker.":"तक्रारी व मार्ग सुचवण्या तपासा आणि क्षेत्र कर्मचाऱ्याला काम द्या.",
      "Start assigned work and submit repair notes with synthetic evidence.":"नियुक्त काम सुरू करून कृत्रिम पुराव्यासह दुरुस्ती नोंदी सादर करा.",
      "Check repair work and approve it or return it for rework.":"दुरुस्ती तपासा आणि मंजूर करा किंवा पुन्हा कामासाठी परतवा.",
      "Review isolated demo metrics and audit activity; global controls are disabled.":"वेगळ्या डेमोचे मेट्रिक्स आणि ऑडिट पाहा; जागतिक नियंत्रणे बंद आहेत.",
      "Choose a role card below to open its isolated portal.":"वेगळे पोर्टल उघडण्यासाठी खालील भूमिका निवडा.",
      "A CLEARER CIVIC LOOP":"अधिक स्पष्ट नागरी प्रक्रिया","From a street-level concern to":"रस्त्यावरील समस्येपासून",
      "accountable action.":"जबाबदार कृतीपर्यंत.","One trackable workflow connects citizen reports, municipal review, field repair and independent inspection.":"एक मागोवा घेता येणारा कार्यप्रवाह नागरिक अहवाल, महानगरपालिका पुनरावलोकन, क्षेत्रीय दुरुस्ती आणि स्वतंत्र तपासणी जोडतो.",
      "Report with evidence":"पुराव्यासह नोंदवा","Route for human review":"मानवी पुनरावलोकनासाठी पाठवा","Verify before closure":"बंद करण्यापूर्वी पडताळा",
      "CITIZEN PORTAL":"नागरिक पोर्टल","MUNICIPAL PORTAL":"महानगरपालिका पोर्टल","FIELD WORKER PORTAL":"क्षेत्र कर्मचारी पोर्टल",
      "INSPECTOR PORTAL":"निरीक्षक पोर्टल","YOUR ACCOUNT":"तुमचे खाते","MEASUREMENT":"मोजमाप",
      "Your civic reports":"तुमच्या नागरी तक्रारी","Track updates from submission through field work and inspection.":"तक्रार नोंदणीपासून क्षेत्रीय काम आणि तपासणीपर्यंतची अद्यतने पाहा.",
      "Track status updates from submission through field work and inspection.":"तक्रार सादरीकरणापासून क्षेत्रीय काम आणि तपासणीपर्यंतच्या स्थितीचे अद्यतन पाहा.",
      "Track updates from submission through field work and inspection.":"तक्रार दाखल केल्यापासून क्षेत्रीय काम व तपासणीपर्यंतचे अद्यतन पाहा.",
      "Refresh status":"स्थिती अद्यतनित करा","Current status":"सध्याची स्थिती","Why it may match:":"साम्याचे कारण:",
      "You can continue to submit a separate report. Continue?":"तुम्ही स्वतंत्र तक्रार सादर करू शकता. पुढे जायचे?",
      "Priority":"प्राधान्य","Department:":"विभाग:","Assigned worker:":"नियुक्त कर्मचारी:",
      "Suggested category · rule-based":"नियमांवर आधारित प्रकार सूचना","A transparent keyword suggestion; not an AI model or an official decision.":"पारदर्शक कीवर्ड सूचना; AI मॉडेल किंवा अधिकृत निर्णय नाही.",
      "Suggested department appears after you select an issue.":"समस्या निवडल्यानंतर सुचवलेला विभाग दिसेल.",
      "Short title":"संक्षिप्त शीर्षक","Ward or locality":"प्रभाग किंवा परिसर","Specific location":"अचूक ठिकाण",
      "What is happening?":"काय घडत आहे?","Latitude":"अक्षांश","Longitude":"रेखांश",
      "PNG, JPEG or WebP · max 1 MB · avoid faces and private information":"PNG, JPEG किंवा WebP · कमाल 1 MB · चेहरे व खाजगी माहिती टाळा",
      "Do not use this form for emergencies. No official government connection is implied.":"आपत्कालीन परिस्थितीसाठी हा फॉर्म वापरू नका. अधिकृत सरकारी जोडणी नाही.",
      "Complaint history":"तक्रार इतिहास","Search your reports":"तुमच्या तक्रारी शोधा","All statuses":"सर्व स्थिती",
      "Submitted":"नोंदवले","Assigned":"नियुक्त","Work in progress":"काम सुरू","Awaiting inspection":"तपासणी प्रलंबित",
      "Rework required":"पुन्हा काम आवश्यक","Resolved":"निराकरण झाले","No complaints in your view":"तुमच्या दृश्यात तक्रारी नाहीत",
      "No assigned work":"नियुक्त काम नाही","No repairs awaiting inspection":"तपासणीसाठी दुरुस्ती नाही",
      "Report a civic issue":"नागरी समस्या नोंदवा","Share a clear location and supporting evidence. Recommendations are reviewed by municipal staff.":"स्पष्ट ठिकाण आणि पूरक पुरावे द्या. शिफारसींचे महानगरपालिका कर्मचारी पुनरावलोकन करतात.",
      "Only work assigned to your account appears in this queue.":"फक्त तुमच्या खात्याला नियुक्त केलेले काम या यादीत दिसते.",
      "Assess the original report and submitted repair evidence. All five checks must pass for approval.":"मूळ तक्रार आणि सादर केलेले दुरुस्ती पुरावे तपासा. मंजुरीसाठी पाचही तपासण्या पास हव्यात.",
      "Work order assigned":"कामाचे आदेश नियुक्त","Work started":"काम सुरू","Repair submitted":"दुरुस्ती सादर",
      "Repair verified":"दुरुस्ती प्रमाणित","Returned for rework":"पुन्हा कामासाठी परतवले",
      "Complaint assigned":"तक्रार नियुक्त","New work assigned":"नवीन काम नियुक्त","Complaint resolved":"तक्रार निकाली",
      "Repair ready for inspection":"दुरुस्ती तपासणीसाठी तयार","Inspection needed":"तपासणी आवश्यक",
      "Rating":"रेटिंग","Submit feedback":"अभिप्राय सादर करा","Optional comment":"ऐच्छिक टिप्पणी",
      "Your rating is separate from the inspection decision and cannot be overwritten after submission.":"तुमचे रेटिंग तपासणी निर्णयापासून स्वतंत्र आहे आणि सादर केल्यानंतर बदलता येत नाही.",
      "Feedback recorded":"अभिप्राय नोंदवला","No written comment.":"लिखित टिप्पणी नाही.",
      "Guided tour complete. You can continue exploring any role.":"मार्गदर्शित फेरफटका पूर्ण. कोणतीही भूमिका पुढे पाहू शकता.",
      "This demo session has been reset.":"हा डेमो सत्र रीसेट झाला आहे.",
      "Reset only this isolated demo session? Its synthetic activity will be replaced; ordinary accounts and records are not affected.":"फक्त हे वेगळे डेमो सत्र रीसेट करायचे? कृत्रिम कृती बदलली जाईल; सामान्य खाती व नोंदींवर परिणाम होणार नाही.",
      "Your reports are private to this demo citizen. Submit a sample complaint to see the real workflow and timeline.":"या डेमो नागरिकाच्या तक्रारी खाजगी आहेत. कार्यप्रवाह व कालरेषा पाहण्यासाठी नमुना तक्रार सादर करा.",
      "Review synthetic submissions and assign only to the field worker created inside this demo session.":"कृत्रिम तक्रारी तपासा आणि फक्त या डेमोमध्ये तयार केलेल्या क्षेत्र कर्मचाऱ्याला नियुक्त करा.",
      "Only work assigned to this demo field-worker account appears here. Repair submissions use the real workflow.":"या डेमो क्षेत्र कर्मचारी खात्याचे कामच येथे दिसते. दुरुस्ती नोंदी खऱ्या कार्यप्रवाहातून जातात.",
      "Review synthetic repair submissions. Inspection decisions are persisted and rework history is retained.":"कृत्रिम दुरुस्ती नोंदी तपासा. तपासणी निर्णय जतन होतात आणि पुन्हा कामाचा इतिहास राहतो.",
      "This restricted demo role can inspect synthetic-only metrics and audit history; global administration is disabled.":"ही मर्यादित डेमो भूमिका फक्त कृत्रिम मेट्रिक्स व ऑडिट पाहू शकते; जागतिक प्रशासन बंद आहे.",
      "Step 1 · Citizen":"टप्पा 1 · नागरिक","Step 2 · Municipal Administrator":"टप्पा 2 · महानगरपालिका प्रशासक",
      "Step 3 · Field Worker":"टप्पा 3 · क्षेत्र कर्मचारी","Step 4 · Inspector":"टप्पा 4 · निरीक्षक",
      "Step 5 · Citizen follow-up":"टप्पा 5 · नागरिक पाठपुरावा","Step 6 · System Administrator":"टप्पा 6 · प्रणाली प्रशासक",
      "Review the synthetic sample reports. You can submit a new demo complaint with a clearly synthetic location and photo.":"कृत्रिम नमुना तक्रारी पाहा. स्पष्टपणे कृत्रिम ठिकाण व छायाचित्रासह नवी डेमो तक्रार नोंदवू शकता.",
      "Review the queue and routing suggestion, then assign a road-work sample to the demo field worker.":"यादी व मार्ग सूचना तपासा आणि रस्त्याच्या नमुना कामाची नियुक्ती डेमो क्षेत्र कर्मचाऱ्याला करा.",
      "Start your assigned sample work, then submit a repair note and synthetic evidence.":"नियुक्त नमुना काम सुरू करून दुरुस्ती नोंद व कृत्रिम पुरावा सादर करा.",
      "Review the repair record and checklist. Approve only when every check passes, or request rework.":"दुरुस्ती नोंद व तपासणी सूची पाहा. सर्व तपासण्या पास झाल्यावरच मंजूर करा, अन्यथा पुन्हा काम मागा.",
      "Review the persisted timeline and notification. A verified sample is available for optional satisfaction feedback.":"जतन केलेली कालरेषा व सूचना पाहा. ऐच्छिक अभिप्रायासाठी प्रमाणित नमुना उपलब्ध आहे.",
      "Explore synthetic-only operational metrics and audit events. Global account and configuration changes are disabled.":"फक्त कृत्रिम कामकाज मेट्रिक्स व ऑडिट पाहा. जागतिक खाते व संरचना बदल बंद आहेत.",
      "Continue tour →":"फेरफटका पुढे →","Finish tour":"फेरफटका पूर्ण करा","Start Guided Tour":"मार्गदर्शित फेरफटका सुरू करा",
      "Explore freely ·":"स्वतंत्रपणे पाहा ·","Tour":"फेरफटका","of 6":"पैकी 6",
      "Current status:":"सध्याची स्थिती:","Why it may match:":"साम्याचे कारण:","similar issue nearby":"जवळची अशीच समस्या",
      "You can continue to submit a separate report. Continue?":"तुम्ही स्वतंत्र तक्रार सादर करू शकता. पुढे जायचे?",
      "Tour":"फेरफटका","Role preview":"भूमिका पूर्वावलोकन","Create staff account":"कर्मचारी खाते तयार करा",
      "User access":"वापरकर्ता प्रवेश","Departments":"विभाग","Routing configuration":"मार्ग संरचना",
      "Recent audit events":"अलीकडील ऑडिट नोंदी","Notification monitoring":"सूचना निरीक्षण",
      "Assign work":"काम नियुक्त करा","Start work":"काम सुरू करा","Completion notes":"काम पूर्णतेची नोंद",
      "After photo evidence":"नंतरचे छायाचित्र पुरावे","Submit for inspection":"तपासणीसाठी सादर करा",
      "Five inspection checks":"पाच तपासणी बाबी","Approve resolution":"निराकरण मंजूर करा",
      "Return for rework":"पुन्हा कामासाठी परतवा","Mark read":"वाचले म्हणून चिन्हांकित करा",
      "New civic complaint":"नवीन नागरी तक्रार","Complaint assigned":"तक्रार नियुक्त","New work assigned":"नवीन काम नियुक्त",
      "Work started":"काम सुरू","Repair ready for inspection":"दुरुस्ती तपासणीसाठी तयार",
      "Inspection needed":"तपासणी आवश्यक","Repair evidence submitted":"दुरुस्ती पुरावा सादर",
      "Complaint resolved":"तक्रार निकाली","Rework requested":"पुन्हा काम मागितले","Inspection completed":"तपासणी पूर्ण",
      "Report submitted":"तक्रार सादर केली","Linked to master issue":"मुख्य समस्येशी जोडले",
      "No workflow history yet.":"अद्याप कार्यप्रवाह इतिहास नाही.",
      "Welcome to the interactive demo":"परस्परसंवादी डेमोमध्ये स्वागत","Synthetic metrics for this isolated interactive session only.":"फक्त या वेगळ्या परस्परसंवादी सत्रातील कृत्रिम मेट्रिक्स.",
      "The request could not be completed. Please retry.":"विनंती पूर्ण करता आली नाही. कृपया पुन्हा प्रयत्न करा.",
      "Issue not found.":"तक्रार सापडली नाही.","Sign in to continue.":"पुढे जाण्यासाठी साइन इन करा.",
      "A similar unresolved report may already exist.":"यासारखी न सुटलेली तक्रार आधीपासून असू शकते.",
      "This complaint has been verified and closed.":"ही तक्रार पडताळून बंद केली आहे.",
      "Next step: municipal review and assignment.":"पुढील टप्पा: महानगरपालिका पुनरावलोकन आणि नियुक्ती.",
      "Next step: the assigned worker can start the work.":"पुढील टप्पा: नियुक्त कर्मचारी काम सुरू करू शकतो.",
      "Next step: the field worker submits repair notes for inspection.":"पुढील टप्पा: क्षेत्र कर्मचारी दुरुस्ती नोंदी तपासणीसाठी सादर करतो.",
      "Next step: an inspector reviews the submitted repair.":"पुढील टप्पा: निरीक्षक सादर केलेली दुरुस्ती तपासतो.",
      "Next step: a worker completes additional work.":"पुढील टप्पा: कर्मचारी अतिरिक्त काम पूर्ण करतो.",
      "{id} is awaiting municipal review.":"{id} महानगरपालिका पुनरावलोकनाच्या प्रतीक्षेत आहे.",
      "{id} was assigned to {department}.":"{id} हे काम {department} विभागाला दिले आहे.",
      "{id} is assigned to you.":"{id} हे काम तुम्हाला दिले आहे.",
      "Field work has started on {id}.":"{id} साठी क्षेत्रीय काम सुरू झाले आहे.",
      "Repair evidence for {id} is awaiting review.":"{id} चा दुरुस्ती पुरावा पुनरावलोकनाच्या प्रतीक्षेत आहे.",
      "{id} is ready for inspection.":"{id} तपासणीसाठी तयार आहे.",
      "{id} is awaiting inspection.":"{id} तपासणीच्या प्रतीक्षेत आहे.",
      "{id} was approved after inspection.":"तपासणीनंतर {id} मंजूर झाले.",
      "{id} was returned for additional work.":"अधिक कामासाठी {id} परत पाठवले.",
      "Inspection of {id} was approved.":"{id} ची तपासणी मंजूर झाली.",
      "Inspection of {id} was returned for rework.":"{id} ची तपासणी पुन्हा कामासाठी परतवली.",
      "All records in this session are synthetic and isolated to this demonstration.":"या सत्रातील सर्व नोंदी कृत्रिम असून या डेमोपुरत्या वेगळ्या आहेत."
    },
    hi: {
      "Language":"भाषा","WELCOME TO NAGRIVANTA":"नाग्रिवंता में आपका स्वागत है","Sign in to your workspace":"अपने कार्यक्षेत्र में साइन इन करें",
      "Use your account to access the right civic workflow.":"सही नागरिक कार्यप्रवाह तक पहुँचने के लिए अपने खाते का उपयोग करें।",
      "Explore Live Demo":"लाइव डेमो देखें","Register as Citizen":"नागरिक के रूप में पंजीकरण करें","Sign In":"साइन इन",
      "Create citizen account":"नागरिक खाता बनाएँ","Email address":"ईमेल पता","Password":"पासवर्ड",
      "Your name":"आपका नाम","Create citizen account →":"नागरिक खाता बनाएँ →",
      "Your account is role-restricted.":"आपके खाते की पहुँच भूमिका के अनुसार सीमित है।",
      "Evidence is private to authorized participants in a complaint.":"साक्ष्य केवल शिकायत के अधिकृत प्रतिभागियों के लिए उपलब्ध हैं।",
      "INTERACTIVE DEMO — Uses synthetic demonstration data.":"इंटरैक्टिव डेमो — कृत्रिम प्रदर्शन डेटा का उपयोग करता है।",
      "Explore Nagrivanta":"नाग्रिवंता देखें","Start Guided Tour":"निर्देशित परिचय शुरू करें","Explore Freely":"स्वतंत्र रूप से देखें",
      "Back to sign in":"साइन इन पर लौटें","Citizen":"नागरिक","Municipal Administrator":"नगरपालिका प्रशासक",
      "Municipal administrator":"नगरपालिका प्रशासक","Field Worker":"फील्ड वर्कर","Field worker":"फील्ड वर्कर",
      "Inspector":"निरीक्षक","System Administrator":"सिस्टम प्रशासक","System administrator":"सिस्टम प्रशासक",
      "Open Citizen portal":"नागरिक पोर्टल खोलें","Open Municipal portal":"नगरपालिका पोर्टल खोलें",
      "Open Field Worker portal":"फील्ड वर्कर पोर्टल खोलें","Open Inspector portal":"निरीक्षक पोर्टल खोलें",
      "Open System Admin portal":"सिस्टम प्रशासक पोर्टल खोलें","Reset demo":"डेमो रीसेट करें","Exit demo":"डेमो से बाहर निकलें",
      "My complaints":"मेरी शिकायतें","Report an issue":"समस्या दर्ज करें","Heritage watch":"विरासत निगरानी",
      "Notifications":"सूचनाएँ","Operations":"कार्य संचालन","Analytics":"विश्लेषण","My work queue":"मेरे कार्य",
      "Inspection queue":"निरीक्षण कतार","Administration":"प्रशासन","Change password":"पासवर्ड बदलें",
      "Sign out":"साइन आउट","Your civic reports":"आपकी नागरिक शिकायतें","Track updates from submission through field work and inspection.":"शिकायत दर्ज होने से लेकर फील्ड कार्य और निरीक्षण तक के अपडेट देखें।",
      "Complaint history":"शिकायत इतिहास","Your submissions only":"केवल आपकी शिकायतें","All statuses":"सभी स्थितियाँ",
      "Submitted":"दर्ज","Assigned":"सौंपा गया","Work in progress":"कार्य जारी","Awaiting inspection":"निरीक्षण लंबित",
      "Rework required":"पुनः कार्य आवश्यक","Resolved":"समाधान हुआ","No complaints yet":"अभी कोई शिकायत नहीं",
      "Submit a civic issue to begin tracking the response.":"प्रतिक्रिया ट्रैक करने के लिए नागरिक समस्या दर्ज करें।",
      "Report a civic issue":"नागरिक समस्या दर्ज करें","Share a clear location and supporting evidence. Recommendations are reviewed by municipal staff.":"सटीक स्थान और सहायक साक्ष्य दें। नगरपालिका कर्मचारी सुझावों की समीक्षा करते हैं।",
      "Issue category and subcategory":"समस्या श्रेणी और उपश्रेणी","Short title":"संक्षिप्त शीर्षक",
      "Ward or locality":"वार्ड या इलाका","Specific location":"सटीक स्थान","What is happening?":"क्या हो रहा है?",
      "Photo evidence":"फ़ोटो साक्ष्य","Submit complaint":"शिकायत जमा करें","Submitting…":"जमा हो रहा है…",
      "How do I submit a complaint?":"शिकायत कैसे जमा करें?","How do I track a complaint?":"शिकायत कैसे ट्रैक करें?",
      "What do statuses mean?":"स्थितियों का क्या अर्थ है?","How do assignment and inspection work?":"कार्य आवंटन और निरीक्षण कैसे होता है?",
      "What happens after rework is requested?":"पुनः कार्य माँगे जाने पर क्या होता है?","How does the demo work?":"डेमो कैसे काम करता है?",
      "Could not load this view":"यह दृश्य लोड नहीं हो सका","Try again":"पुनः प्रयास करें",
      "Feedback":"प्रतिक्रिया","Submit feedback":"प्रतिक्रिया जमा करें","Rating":"रेटिंग",
      "No new update is available yet.":"अभी कोई नया अपडेट उपलब्ध नहीं है।",
      "A similar unresolved report may already exist.":"ऐसी ही एक अनसुलझी शिकायत पहले से हो सकती है।",
      "Thank you. Your feedback was recorded.":"धन्यवाद। आपकी प्रतिक्रिया दर्ज कर ली गई है।",
      "See how a public issue can move through citizen reporting, municipal review, field work, inspection, and resolution. This is an isolated demo, not live government activity.":"देखें कि नागरिक रिपोर्ट, नगरपालिका समीक्षा, फील्ड कार्य, निरीक्षण और समाधान कैसे जुड़ते हैं। यह अलग डेमो है, सरकारी गतिविधि नहीं।",
      "Submit and track an issue; receive updates and rate a verified resolution.":"समस्या दर्ज करें, ट्रैक करें, अपडेट पाएँ और सत्यापित समाधान को रेट करें।",
      "Review reports, routing suggestions, and assign a field worker.":"रिपोर्ट और रूटिंग सुझाव देखें तथा फील्ड वर्कर को काम दें।",
      "Start assigned work and submit repair notes with synthetic evidence.":"सौंपा गया काम शुरू करें और कृत्रिम साक्ष्य के साथ मरम्मत नोट भेजें।",
      "Check repair work and approve it or return it for rework.":"मरम्मत जाँचें और स्वीकृत करें या दोबारा काम के लिए लौटाएँ।",
      "Review isolated demo metrics and audit activity; global controls are disabled.":"अलग डेमो मेट्रिक्स और ऑडिट देखें; वैश्विक नियंत्रण बंद हैं।",
      "Choose a role card below to open its isolated portal.":"अलग पोर्टल खोलने के लिए नीचे की भूमिका चुनें।",
      "A CLEARER CIVIC LOOP":"अधिक स्पष्ट नागरिक प्रक्रिया","accountable action.":"जवाबदेह कार्रवाई तक।",
      "Report with evidence":"साक्ष्य सहित दर्ज करें","Route for human review":"मानव समीक्षा के लिए भेजें","Verify before closure":"बंद करने से पहले सत्यापित करें",
      "CITIZEN PORTAL":"नागरिक पोर्टल","MUNICIPAL PORTAL":"नगरपालिका पोर्टल","FIELD WORKER PORTAL":"फील्ड वर्कर पोर्टल",
      "INSPECTOR PORTAL":"निरीक्षक पोर्टल","YOUR ACCOUNT":"आपका खाता","MEASUREMENT":"मापन",
      "Refresh status":"स्थिति ताज़ा करें","Current status":"वर्तमान स्थिति","Why it may match:":"मेल का कारण:",
      "You can continue to submit a separate report. Continue?":"आप अलग शिकायत जमा कर सकते हैं। आगे बढ़ें?",
      "Priority":"प्राथमिकता","Department:":"विभाग:","Assigned worker:":"सौंपा गया कर्मचारी:",
      "Suggested category · rule-based":"नियम-आधारित श्रेणी सुझाव","A transparent keyword suggestion; not an AI model or an official decision.":"पारदर्शी कीवर्ड सुझाव; AI मॉडल या आधिकारिक निर्णय नहीं।",
      "Suggested department appears after you select an issue.":"समस्या चुनने के बाद सुझाया गया विभाग दिखाई देगा।",
      "Latitude":"अक्षांश","Longitude":"देशांतर",
      "PNG, JPEG or WebP · max 1 MB · avoid faces and private information":"PNG, JPEG या WebP · अधिकतम 1 MB · चेहरे और निजी जानकारी से बचें",
      "Do not use this form for emergencies. No official government connection is implied.":"आपातकाल में इस फ़ॉर्म का उपयोग न करें। कोई आधिकारिक सरकारी जुड़ाव नहीं है।",
      "Search your reports":"अपनी शिकायतें खोजें","No complaints in your view":"आपके दृश्य में कोई शिकायत नहीं",
      "No assigned work":"कोई काम नहीं सौंपा गया","No repairs awaiting inspection":"निरीक्षण के लिए कोई मरम्मत लंबित नहीं",
      "Only work assigned to your account appears in this queue.":"इस कतार में केवल आपके खाते को सौंपा गया काम दिखता है।",
      "Assess the original report and submitted repair evidence. All five checks must pass for approval.":"मूल रिपोर्ट और जमा मरम्मत साक्ष्य जाँचें। स्वीकृति के लिए सभी पाँच जाँच पास होनी चाहिए।",
      "Work order assigned":"कार्य आदेश सौंपा गया","Work started":"काम शुरू","Repair submitted":"मरम्मत जमा",
      "Repair verified":"मरम्मत सत्यापित","Returned for rework":"दोबारा काम के लिए लौटाया",
      "Complaint assigned":"शिकायत सौंप दी गई","New work assigned":"नया काम सौंपा गया","Complaint resolved":"शिकायत हल हुई",
      "Repair ready for inspection":"मरम्मत निरीक्षण के लिए तैयार","Inspection needed":"निरीक्षण आवश्यक",
      "Optional comment":"वैकल्पिक टिप्पणी","Your rating is separate from the inspection decision and cannot be overwritten after submission.":"आपकी रेटिंग निरीक्षण निर्णय से अलग है और जमा करने के बाद बदली नहीं जा सकती।",
      "Feedback recorded":"प्रतिक्रिया दर्ज","No written comment.":"कोई लिखित टिप्पणी नहीं।",
      "Guided tour complete. You can continue exploring any role.":"निर्देशित परिचय पूरा। आप किसी भी भूमिका को देख सकते हैं।",
      "This demo session has been reset.":"यह डेमो सत्र रीसेट हो गया है।",
      "Your reports are private to this demo citizen. Submit a sample complaint to see the real workflow and timeline.":"इस डेमो नागरिक की शिकायतें निजी हैं। वास्तविक कार्यप्रवाह और टाइमलाइन देखने के लिए नमूना शिकायत दर्ज करें।",
      "Review synthetic submissions and assign only to the field worker created inside this demo session.":"कृत्रिम शिकायतें देखें और केवल इसी डेमो के फील्ड वर्कर को काम सौंपें।",
      "Only work assigned to this demo field-worker account appears here. Repair submissions use the real workflow.":"यहाँ केवल इस डेमो फील्ड वर्कर को सौंपा गया काम दिखता है। मरम्मत वास्तविक कार्यप्रवाह में दर्ज होती है।",
      "Review synthetic repair submissions. Inspection decisions are persisted and rework history is retained.":"कृत्रिम मरम्मत प्रविष्टियाँ देखें। निरीक्षण निर्णय सहेजे जाते हैं और पुनः कार्य इतिहास बना रहता है।",
      "This restricted demo role can inspect synthetic-only metrics and audit history; global administration is disabled.":"यह सीमित डेमो भूमिका केवल कृत्रिम मेट्रिक्स और ऑडिट देख सकती है; वैश्विक प्रशासन बंद है।",
      "Step 1 · Citizen":"चरण 1 · नागरिक","Step 2 · Municipal Administrator":"चरण 2 · नगरपालिका प्रशासक",
      "Step 3 · Field Worker":"चरण 3 · फील्ड वर्कर","Step 4 · Inspector":"चरण 4 · निरीक्षक",
      "Step 5 · Citizen follow-up":"चरण 5 · नागरिक फ़ॉलो-अप","Step 6 · System Administrator":"चरण 6 · सिस्टम प्रशासक",
      "Review the synthetic sample reports. You can submit a new demo complaint with a clearly synthetic location and photo.":"कृत्रिम नमूना रिपोर्ट देखें। स्पष्ट कृत्रिम स्थान और फ़ोटो के साथ नई डेमो शिकायत दर्ज कर सकते हैं।",
      "Review the queue and routing suggestion, then assign a road-work sample to the demo field worker.":"कतार और रूटिंग सुझाव देखें, फिर सड़क कार्य डेमो फील्ड वर्कर को सौंपें।",
      "Start your assigned sample work, then submit a repair note and synthetic evidence.":"सौंपा नमूना काम शुरू करें, फिर मरम्मत नोट और कृत्रिम साक्ष्य जमा करें।",
      "Review the repair record and checklist. Approve only when every check passes, or request rework.":"मरम्मत रिकॉर्ड और जाँच सूची देखें। सभी जाँच पास होने पर ही मंजूर करें, अन्यथा पुनः कार्य माँगें।",
      "Review the persisted timeline and notification. A verified sample is available for optional satisfaction feedback.":"सहेजी गई टाइमलाइन और सूचना देखें। वैकल्पिक संतुष्टि प्रतिक्रिया के लिए सत्यापित नमूना उपलब्ध है।",
      "Explore synthetic-only operational metrics and audit events. Global account and configuration changes are disabled.":"केवल कृत्रिम संचालन मेट्रिक्स और ऑडिट देखें। वैश्विक खाता और कॉन्फ़िगरेशन बदलाव बंद हैं।",
      "Continue tour →":"परिचय जारी रखें →","Finish tour":"परिचय समाप्त करें","Explore freely ·":"स्वतंत्र रूप से देखें ·","Tour":"परिचय","of 6":"में से 6",
      "Current status:":"वर्तमान स्थिति:","Why it may match:":"मेल का कारण:","similar issue nearby":"पास की मिलती-जुलती समस्या",
      "You can continue to submit a separate report. Continue?":"आप अलग शिकायत जमा कर सकते हैं। आगे बढ़ें?",
      "Role preview":"भूमिका पूर्वावलोकन","Create staff account":"स्टाफ खाता बनाएँ","User access":"उपयोगकर्ता पहुँच",
      "Departments":"विभाग","Routing configuration":"रूटिंग कॉन्फ़िगरेशन","Recent audit events":"हाल की ऑडिट गतिविधि",
      "Notification monitoring":"सूचना निगरानी","Assign work":"काम सौंपें","Start work":"काम शुरू करें",
      "Completion notes":"कार्य-पूर्णता नोट","After photo evidence":"बाद की फ़ोटो का साक्ष्य","Submit for inspection":"निरीक्षण के लिए जमा करें",
      "Five inspection checks":"पाँच निरीक्षण जाँच","Approve resolution":"समाधान स्वीकृत करें",
      "Return for rework":"दोबारा काम के लिए लौटाएँ","Mark read":"पढ़ा हुआ चिह्नित करें",
      "New civic complaint":"नई नागरिक शिकायत","Complaint assigned":"शिकायत सौंप दी गई","New work assigned":"नया काम सौंपा गया",
      "Work started":"काम शुरू","Repair ready for inspection":"मरम्मत निरीक्षण के लिए तैयार","Inspection needed":"निरीक्षण आवश्यक",
      "Repair evidence submitted":"मरम्मत साक्ष्य जमा","Complaint resolved":"शिकायत हल हुई",
      "Rework requested":"पुनः कार्य माँगा गया","Inspection completed":"निरीक्षण पूरा",
      "Report submitted":"शिकायत जमा की गई","Linked to master issue":"मुख्य समस्या से जोड़ा गया",
      "No workflow history yet.":"अभी तक कोई कार्यप्रवाह इतिहास नहीं है।",
      "Welcome to the interactive demo":"इंटरैक्टिव डेमो में आपका स्वागत","Synthetic metrics for this isolated interactive session only.":"केवल इस अलग इंटरैक्टिव सत्र के कृत्रिम मेट्रिक्स।",
      "The request could not be completed. Please retry.":"अनुरोध पूरा नहीं हो सका। कृपया फिर प्रयास करें।",
      "Issue not found.":"शिकायत नहीं मिली।","Sign in to continue.":"आगे बढ़ने के लिए साइन इन करें.",
      "This complaint has been verified and closed.":"इस शिकायत का सत्यापन कर इसे बंद कर दिया गया है।",
      "Next step: municipal review and assignment.":"अगला चरण: नगरपालिका समीक्षा और आवंटन।",
      "Next step: the assigned worker can start the work.":"अगला चरण: सौंपा गया कर्मचारी काम शुरू कर सकता है।",
      "Next step: the field worker submits repair notes for inspection.":"अगला चरण: फील्ड वर्कर मरम्मत नोट निरीक्षण के लिए भेजता है।",
      "Next step: an inspector reviews the submitted repair.":"अगला चरण: निरीक्षक जमा मरम्मत की समीक्षा करता है।",
      "Next step: a worker completes additional work.":"अगला चरण: कर्मचारी अतिरिक्त कार्य पूरा करता है।",
      "{id} is awaiting municipal review.":"{id} नगरपालिका समीक्षा की प्रतीक्षा में है।",
      "{id} was assigned to {department}.":"{id} को {department} विभाग को सौंपा गया है।",
      "{id} is assigned to you.":"{id} आपको सौंपा गया है।",
      "Field work has started on {id}.":"{id} पर फील्ड कार्य शुरू हो गया है।",
      "Repair evidence for {id} is awaiting review.":"{id} का मरम्मत साक्ष्य समीक्षा की प्रतीक्षा में है।",
      "{id} is ready for inspection.":"{id} निरीक्षण के लिए तैयार है।",
      "{id} is awaiting inspection.":"{id} निरीक्षण की प्रतीक्षा में है।",
      "{id} was approved after inspection.":"निरीक्षण के बाद {id} स्वीकृत हुआ।",
      "{id} was returned for additional work.":"अतिरिक्त कार्य के लिए {id} लौटाया गया।",
      "Inspection of {id} was approved.":"{id} का निरीक्षण स्वीकृत हुआ।",
      "Inspection of {id} was returned for rework.":"{id} का निरीक्षण दोबारा काम के लिए लौटाया गया।",
      "All records in this session are synthetic and isolated to this demonstration.":"इस सत्र के सभी रिकॉर्ड कृत्रिम हैं और इस डेमो तक अलग रखे गए हैं।"
    }
  };

  const storageKey = "nagrivanta.language";
  function get() {
    try { const value = localStorage.getItem(storageKey); return ["en","mr","hi"].includes(value) ? value : "en"; }
    catch { return "en"; }
  }
  function set(language) {
    const next = ["en","mr","hi"].includes(language) ? language : "en";
    try { localStorage.setItem(storageKey,next); } catch {}
    document.documentElement.lang = next;
    document.querySelectorAll("#languageSelect,#languageSelectAuth").forEach(select => { select.value = next; });
    apply(document);
    document.dispatchEvent(new CustomEvent("nagrivanta-language-change",{detail:{language:next}}));
  }
  function apply(root) {
    const language = get();
    const dictionary = dictionaries[language] || {};
    const englishFromTranslation = new Map();
    for (const [lang,entries] of Object.entries(dictionaries)) {
      for (const [english,translated] of Object.entries(entries)) englishFromTranslation.set(translated,english);
    }
    const walker = document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (node.parentElement?.closest("script,style,.report-summary,.assistant-answer,.user-content,.timeline p,.note-box p,.report-card h3")) continue;
      const current = node.nodeValue;
      const trimmed = current.trim();
      const english = englishFromTranslation.get(trimmed) || trimmed;
      if (!Object.prototype.hasOwnProperty.call(dictionaries.mr,english) &&
          !Object.prototype.hasOwnProperty.call(dictionaries.hi,english)) continue;
      node.nodeValue = current.replace(trimmed,dictionary[english] || english);
    }
    const attrs = ["placeholder","aria-label","title"];
    root.querySelectorAll?.("*").forEach(el => {
      if (el.matches(".report-summary,.assistant-answer,.user-content")) return;
      for (const attr of attrs) {
        const current = el.getAttribute(attr);
        if (!current) continue;
        const english = englishFromTranslation.get(current) || current;
        if (Object.prototype.hasOwnProperty.call(dictionaries.mr,english) ||
            Object.prototype.hasOwnProperty.call(dictionaries.hi,english)) el.setAttribute(attr,dictionary[english] || english);
      }
    });
  }
  window.NagrivantaI18n = {get,set,apply,translations:dictionaries};
  document.documentElement.lang = get();
  document.addEventListener("DOMContentLoaded",() => {
    document.querySelectorAll("#languageSelect,#languageSelectAuth").forEach(select => { select.value=get(); });
    apply(document);
    new MutationObserver(records => records.forEach(record => {
      if (record.type === "childList") record.addedNodes.forEach(node => {
        if (node.nodeType === Node.ELEMENT_NODE) apply(node);
        else if (node.nodeType === Node.TEXT_NODE) apply(node.parentElement || document);
      });
    })).observe(document.body,{childList:true,subtree:true});
  },{once:true});
})();