/**
 * create_form.gs — Google Apps Script that builds the Track A survey form.
 *
 * HOW TO RUN (Sahaj):
 *   1. Go to https://script.google.com  ->  New project.
 *   2. Paste this whole file, save.
 *   3. Run `createForm`. Authorise when prompted.
 *   4. The Logs (View > Logs / Executions) print the form's edit URL,
 *      published URL, and the linked response-sheet URL.
 *   5. Fill ONE test response, check the sheet, then delete that response.
 *
 * Design (from questionnaire.md):
 *   - Open/unprompted questions come BEFORE any closed categories.
 *   - Screening branches; NO ONE is dropped for being Paytm-primary.
 *   - 10 repeated payment sections (amount, type, app, why).
 *   - Neutral concept card is LAST.
 *   - Group (G1/G2/G3) is NOT asked; it is derived later in ingest.py from
 *     the primary-app answer and the "Paytm in last 90 days" answer.
 */

function createForm() {
  var form = FormApp.create('UPI Payments — College Student Survey');
  form.setDescription(
    'Voluntary academic research on how college students use UPI apps. ' +
    'You can skip any question or stop anytime. We do NOT collect your name, ' +
    'phone, email, or UPI ID. Responses are anonymous and reported only in ' +
    'aggregate. The idea at the end is hypothetical, not a real product.'
  );
  form.setProgressBar(true);
  form.setCollectEmail(false);       // keep it anonymous
  form.setLimitOneResponsePerUser(false);

  // ---- Page break items (create up front so we can navigate to them) ----
  var pgUpi30    = form.addPageBreakItem().setTitle('UPI usage');
  var pgInstall  = form.addPageBreakItem().setTitle('Paytm on your phone');
  var pgShort    = form.addPageBreakItem().setTitle('A couple of quick questions');
  var pgFull     = form.addPageBreakItem().setTitle('Your main app');
  var pgOpen     = form.addPageBreakItem().setTitle('In your own words');
  var pgPayIntro = form.addPageBreakItem().setTitle('Your last 10 UPI payments');
  var payPages   = [];
  for (var i = 1; i <= 10; i++) {
    payPages.push(form.addPageBreakItem().setTitle('Payment ' + i + ' of 10'));
  }
  var pgContext  = form.addPageBreakItem().setTitle('A bit about you');
  var pgConcept  = form.addPageBreakItem().setTitle('One idea to react to');

  // =====================================================================
  // SECTION 1 — SCREENING (kept for rates; no one is dropped)
  // =====================================================================

  // Q1 college student  (branch: No -> SUBMIT)
  var q1 = form.addMultipleChoiceItem().setTitle('Are you currently a college student?');
  q1.setChoices([
    q1.createChoice('Yes', pgUpi30),
    q1.createChoice('No',  FormApp.PageNavigationType.SUBMIT)
  ]);

  // ---- Page: UPI in last 30 days (branch: No -> SUBMIT) ----
  form.addSectionHeaderItem().setTitle('Screening');
  var q2 = form.addMultipleChoiceItem().setTitle('Have you made a UPI payment in the last 30 days?');
  q2.setChoices([
    q2.createChoice('Yes', pgInstall),
    q2.createChoice('No',  FormApp.PageNavigationType.SUBMIT)
  ]);
  pgUpi30.setGoToPage(pgInstall);

  // ---- Page: Paytm installed? (branch: Yes -> full path, No -> short path) ----
  var q3 = form.addMultipleChoiceItem().setTitle('Is Paytm installed on your phone?');
  q3.setChoices([
    q3.createChoice('Yes', pgFull),
    q3.createChoice('No',  pgShort)
  ]);
  pgInstall.setGoToPage(pgFull);

  // ---- Short path (Paytm not installed): primary app + one open Q, then end ----
  var q5s = form.addMultipleChoiceItem()
    .setTitle('Which app did you use for MOST of your UPI payments in the last month?');
  q5s.setChoices([
    q5s.createChoice('PhonePe'), q5s.createChoice('GPay'),
    q5s.createChoice('Paytm'),   q5s.createChoice('BHIM'),
    q5s.createChoice('Other')
  ]);
  form.addParagraphTextItem()
    .setTitle('What is the main reason Paytm is not on your phone?');
  pgShort.setGoToPage(FormApp.PageNavigationType.SUBMIT);

  // ---- Full path: Paytm-in-90-days + primary app ----
  var q4 = form.addMultipleChoiceItem()
    .setTitle('Have you made a UPI payment with Paytm in the last 90 days?');
  q4.setChoices([q4.createChoice('Yes'), q4.createChoice('No')]);
  var q5 = form.addMultipleChoiceItem()
    .setTitle('Which app did you use for MOST of your UPI payments in the last month?');
  q5.setChoices([
    q5.createChoice('PhonePe'), q5.createChoice('GPay'),
    q5.createChoice('Paytm'),   q5.createChoice('BHIM'),
    q5.createChoice('Other')
  ]);
  pgFull.setGoToPage(pgOpen);

  // =====================================================================
  // SECTION 2 — UNPROMPTED (open text, no options) — BEFORE closed Qs
  // =====================================================================
  form.addSectionHeaderItem().setTitle('In your own words')
    .setHelpText('Please type freely — there are no options to pick from here.');
  form.addParagraphTextItem().setTitle(
    'For everyday payments, what is the single biggest reason you use your main ' +
    'app instead of the others? (If your main app IS Paytm, tell us why Paytm ' +
    'rather than the other apps.)');
  form.addParagraphTextItem().setTitle('When did you last use Paytm, and for what?');
  form.addParagraphTextItem().setTitle(
    'Have you ever switched your primary UPI app? If yes: from which app to ' +
    'which, roughly when, and what caused the switch?');
  pgOpen.setGoToPage(pgPayIntro);

  // =====================================================================
  // SECTION 3 — LAST 10 UPI PAYMENTS
  // =====================================================================
  pgPayIntro.setHelpText(
    'Open your UPI app history. For each of your last 10 payments, fill the ' +
    'four fields. Amount is a number in rupees.');
  var amountValidation = FormApp.createTextValidation()
    .setHelpText('Enter a number (rupees).').requireNumber().build();

  for (var p = 0; p < 10; p++) {
    var amt = form.addTextItem().setTitle('Payment ' + (p + 1) + ' — Amount (₹)');
    amt.setValidation(amountValidation);
    var typ = form.addMultipleChoiceItem().setTitle('Payment ' + (p + 1) + ' — Type');
    typ.setChoices([
      typ.createChoice('Merchant'), typ.createChoice('P2P (friend/family)'),
      typ.createChoice('Bill'), typ.createChoice('Recharge'), typ.createChoice('Other')
    ]);
    var app = form.addMultipleChoiceItem().setTitle('Payment ' + (p + 1) + ' — App used');
    app.setChoices([
      app.createChoice('PhonePe'), app.createChoice('GPay'),
      app.createChoice('Paytm'), app.createChoice('BHIM'), app.createChoice('Other')
    ]);
    form.addTextItem().setTitle('Payment ' + (p + 1) + ' — Why that app?');
    // chain to next payment page, last one -> context
    if (p < 9) { payPages[p].setGoToPage(payPages[p + 1]); }
    else       { payPages[p].setGoToPage(pgContext); }
  }

  // =====================================================================
  // SECTION 4 — CONTEXT (closed)
  // =====================================================================
  var yr = form.addMultipleChoiceItem().setTitle('Year of study');
  yr.setChoices(['1st','2nd','3rd','4th','5th+'].map(function(v){return yr.createChoice(v);}));
  var hd = form.addMultipleChoiceItem().setTitle('Hostel or day scholar?');
  hd.setChoices([hd.createChoice('Hostel'), hd.createChoice('Day scholar')]);
  form.addTextItem().setTitle('Home state');
  form.addTextItem().setTitle('College');

  var fail = form.addMultipleChoiceItem()
    .setTitle('Has a UPI payment failed for you in the last 3 months?');
  fail.setChoices([fail.createChoice('Yes'), fail.createChoice('No')]);
  form.addTextItem().setTitle('If yes — which app, and what did you do next?');

  var fund = form.addMultipleChoiceItem().setTitle('How is your monthly spending mostly funded?');
  fund.setChoices([
    fund.createChoice("Parents' regular allowance"),
    fund.createChoice('Parents send when asked'),
    fund.createChoice('Own income'), fund.createChoice('Scholarship'),
    fund.createChoice('Mix')
  ]);
  var reach = form.addMultipleChoiceItem().setTitle('How does money from parents reach you?');
  reach.setChoices([
    reach.createChoice('UPI — see next question for which app'),
    reach.createChoice('Bank transfer'), reach.createChoice('Cash'),
    reach.createChoice('Not applicable')
  ]);
  form.addTextItem().setTitle('If parents send money via UPI, which app?');
  var pp = form.addMultipleChoiceItem().setTitle('Does either parent use Paytm?');
  pp.setChoices([
    pp.createChoice('Yes'), pp.createChoice('No'), pp.createChoice('Not sure')
  ]);
  form.addTextItem().setTitle('If yes — what do they use Paytm for?');
  var split = form.addMultipleChoiceItem()
    .setTitle('How often do you split payments with friends in a week?');
  split.setChoices(['0','1–2','3–5','6+'].map(function(v){return split.createChoice(v);}));
  pgContext.setGoToPage(pgConcept);

  // =====================================================================
  // SECTION 5 — NEUTRAL CONCEPT TEST (last)
  // =====================================================================
  pgConcept.setHelpText(
    'Imagine Paytm allowed a parent to give a student a monthly spending limit ' +
    'from the parent\'s bank account. The student could make UPI payments ' +
    'within that limit. (This is a hypothetical idea, not a real product.)');
  var use = form.addScaleItem().setTitle('Would you use it?')
    .setBounds(1, 5).setLabels('Definitely not', 'Definitely yes');
  form.addParagraphTextItem().setTitle('What would concern you about it?');
  form.addParagraphTextItem().setTitle('What would make you use it?');
  var vis = form.addMultipleChoiceItem()
    .setTitle('Would you prefer your parent to see…');
  vis.setChoices([
    vis.createChoice('Each payment'), vis.createChoice('Weekly category totals'),
    vis.createChoice('Only the total')
  ]);
  var agree = form.addMultipleChoiceItem()
    .setTitle('Who would need to agree to set it up?');
  agree.setChoices([
    agree.createChoice('You'), agree.createChoice('Your parent'),
    agree.createChoice('Both')
  ]);

  // ---- Create a linked response spreadsheet ----
  var ss = SpreadsheetApp.create('UPI Survey — Responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  Logger.log('Form edit URL:      ' + form.getEditUrl());
  Logger.log('Form published URL: ' + form.getPublishedUrl());
  Logger.log('Responses sheet:    ' + ss.getUrl());
}
