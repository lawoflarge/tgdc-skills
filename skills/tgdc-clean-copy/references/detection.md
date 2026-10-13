# Detection reference

## B8. Detection reference

Normalize both the terms and the text before matching: lowercase, fold diacritics, and treat ä as ae, ö as oe, ü as ue, ß as ss. Match folder and file-name terms as whole tokens (split on spaces, `_`, `-`, `.`, digits, and case changes), so Lohn does not hit Lohnfertigung. Report hits on short or ambiguous tokens (ID, RG, L4, AU, Personal, Pass) separately so the operator can judge them. The lists below are starters: extend them to every language in LANGUAGES. Weight hits in titles, the first 15 lines of a page, file names, and folder names higher.

**Folder and file-name gates**
- HR and pay: HR, Human Resources, Personal, Personalabteilung, Personalakte, Mitarbeiter, Lohn, Gehalt, Payroll, Lohnbuchhaltung, Entgelt, Bewerbung, Bewerber, Recruiting, Zeugnisse, Urlaub, Krankmeldung; RH, Ressources Humaines, Paie, Salaires; RRHH, Recursos Humanos, Nóminas; Folha de Pagamento, Holerites, Departamento Pessoal; Kadry, Płace, Wynagrodzenia, Rekrutacja; Personeelszaken, Salarissen, Sollicitaties
- Identity and health: Ausweis, Ausweise, Reisepass, Passport, CNI, DNI, CNH, Dowody; Arzt, Medical, Gesundheit, Krankenkasse, Rezepte, Arbeitsmedizin, Santé, Mutuelle, Salud, Saúde, Zdrowie
- Private: Privat, Private, Persönlich, Privé, Prywatne

**Document-type terms**
- Pay: Gehaltsabrechnung, Lohnabrechnung, Entgeltabrechnung, Lohnsteuerbescheinigung, Lohnjournal, Personalkosten; payslip, pay stub, payroll, W-2, P60; bulletin de paie, fiche de paie; nómina, recibo de salarios; holerite, contracheque, folha de pagamento; pasek wypłaty, lista płac, PIT-11, ZUS RMUA; loonstrook, salarisstrook. Transfer purposes: Gehalt, Lohn, Löhnung, Vorschuss, salary, salaire, salario, salário, wynagrodzenie, pensja, salaris, loon.
- Personnel: Arbeitsvertrag, Änderungsvertrag, Aufhebungsvertrag, Kündigung, Abmahnung, Arbeitszeugnis, Personalbogen, Personalfragebogen, Führungszeugnis, Lebenslauf, Freelance-Vertrag, Freelancervertrag, Honorarvertrag, Vertrag über freie Mitarbeit, Dienstvertrag (with a natural person); employment contract, freelance agreement, independent contractor agreement, consultancy agreement with an individual, offer letter, termination, warning letter, performance review, reference letter, CV, resume, cover letter; contrat de travail, licenciement, lettre de motivation; contrato de trabajo, despido, finiquito, currículum; contrato de trabalho, contrato de prestação de serviços com pessoa física, rescisão, currículo, CTPS; umowa o pracę, umowa zlecenie, umowa o dzieło, świadectwo pracy, wypowiedzenie, kwestionariusz osobowy; arbeidsovereenkomst, ontslag, sollicitatie.
- Contract counterparty: a contract (Vertrag, agreement, contrat, contrato, umowa) whose party block names a natural person, without a company legal form such as GmbH, AG, KG, Ltd, LLC, SA, Sp. z o.o., or Ltda, or that says Einzelunternehmer, sole trader, freelancer, or Auftragnehmer followed by a personal name, is P2.
- Leave and health: Urlaubsantrag, Krankmeldung, Arbeitsunfähigkeitsbescheinigung, AU-Bescheinigung, Rezept, Privatrezept, Arztbrief, Befund, Diagnose, Attest, Versichertenkarte, Schwerbehindertenausweis; leave request, vacation request, sick note, medical certificate, prescription, diagnosis; demande de congés, arrêt de travail, ordonnance, certificat médical, carte vitale; solicitud de vacaciones, baja médica, receta, informe médico; férias, atestado médico, receita, laudo, plano de saúde; wniosek urlopowy, zwolnienie lekarskie, e-ZLA, recepta, zaświadczenie lekarskie; verlofaanvraag, ziekmelding, doktersverklaring.
- Identity: Personalausweis, Reisepass, Aufenthaltstitel, Führerschein, Meldebescheinigung; passport, identity card, driver's license, residence permit, visa; carte nationale d'identité, titre de séjour, permis de conduire; DNI, NIE, pasaporte; RG, CNH, carteira de identidade; dowód osobisty, paszport, karta pobytu, prawo jazdy; identiteitskaart, paspoort, verblijfsvergunning, rijbewijs. Country headers such as "Bundesrepublik Deutschland", "Rzeczpospolita Polska", "República Federativa do Brasil".
- Tables of people: two or more of personnel number, first or last name, date of birth, tax class, social security number, tax ID, health insurer, gross, net, salary, private IBAN, home address, entry or exit date, vacation days, sick days, with many rows. Any table, even with two rows, that lists named persons with pay data (gross, net, salary, tax class, private IBAN) is P1. Check hidden sheets too.

**Validated identifiers** (use `python-stdnum`; a checksum-valid personal ID is a strong signal, two different ones nearly certain)
- Personal: German tax ID (`de.idnr`), US SSN, Brazil CPF (`br.cpf`), Polish PESEL, French NIR, Dutch BSN, Indian Aadhaar, Spanish DNI and NIE, dates of birth near "geb.", "geboren", "Geburtsdatum", "date of birth", "né le", "fecha de nacimiento", "data de nascimento", "data urodzenia", "geboortedatum".
- Machine-readable zone of ID documents: lines of 28 to 46 characters from `A-Z0-9<` with runs of `<` (for example `P<DEU`, `IDD<<`). Validate check digits (7-3-1) after normalizing OCR confusions. A failed checksum still sends the page to the review list.
- Ambiguous: IBAN (company accounts are on every invoice; it counts only next to salary terms or a private account holder), private email domains (gmx, web.de, gmail, wp.pl, hotmail), phone numbers.
- Business identifiers are never personal signals: VAT IDs, Brazil CNPJ, SIREN or SIRET, commercial register numbers, EORI, GLN, container numbers.

**Images**
Identity documents are found by the shipped script `scripts/id_signals.py` (Phase 4). It renders every page and image in four orientations, detects faces with the OpenCV Haar cascade bundled in `opencv-python-headless` 4.x (version 5 no longer ships it), reads machine-readable zones and validates their check digits, and tells document pages from photos by their share of white background. A face plus a machine-readable zone or identity terms means P4. A face on a scanned page with little readable text goes to the review list. A face in a photo, brochure, or presentation is copied.

**NDAs**
- Titles (count only in the file name, the document title, an email subject, or the first lines of page 1; never in an email footer, a signature block, or quoted text): Geheimhaltungsvereinbarung, Vertraulichkeitsvereinbarung, Verschwiegenheitserklärung, non-disclosure agreement, NDA, confidentiality agreement, mutual NDA, accord de confidentialité, acuerdo de confidencialidad, acordo de confidencialidade, termo de confidencialidade, umowa o zachowaniu poufności, geheimhoudingsovereenkomst.
- Statements of NDA material: "under NDA", "subject to the NDA", "pursuant to the confidentiality agreement", "gemäß Geheimhaltungsvereinbarung", "sous accord de confidentialité", "conforme acordo de confidencialidade", in a title, subject line, banner, or the top of page 1. The same words in an email footer are boilerplate and do not count.
- Plain "confidential" or "vertraulich" markings alone do not make a file NDA material.

**Known traps** (each one caused a real miss in an earlier screening)
- ID copies attached as later pages inside loading and shipping papers. Page 1 was clean.
- Health records in files named `07.pdf` or `scan0105.pdf`. File names said nothing.
- Noisy ID scans that the text layer read as empty. The machine-readable zone and the face caught them.
- An ID card or stamp rotated 90 degrees that standard OCR did not read.
- Personal data only in an attachment of an email, or a member of a ZIP.
- Salary transfers that look like any other bank payment slip. Only the purpose field ("Gehalt", "Lohn") shows it.
- Over-exclusion: partner names, generic words in folder names, and author metadata are not personal data files. Check gate hits by folder before applying them widely.
