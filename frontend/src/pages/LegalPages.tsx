import React from 'react';
import { Link } from 'react-router-dom';

export function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      <h1 className="text-3xl font-bold text-white mb-2">Privacy Policy</h1>
      <p className="text-slate-500 text-sm mb-8">Last updated: October 2026</p>

      <div className="prose prose-invert prose-sm max-w-none space-y-6 text-slate-300">
        <section>
          <h2 className="text-xl font-semibold text-white mb-3">1. Data We Collect</h2>
          <p>CareerCompass collects: your email address, full name, academic profile (degree, semester, CGPA), answers to the RIASEC interest questionnaire, skill self-ratings, and booking information. All data is stored securely and used only to provide career guidance.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">2. How We Use Your Data</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>Generating personalised career recommendations</li>
            <li>Providing skill-gap analysis and learning roadmaps</li>
            <li>Enabling counsellor booking (only with your explicit consent)</li>
            <li>Improving our recommendation algorithms (anonymised)</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">3. Counsellor Consent</h2>
          <p>Your RIASEC results and assessment data are <strong>never shared</strong> with a counsellor without your explicit, per-booking consent. You can revoke consent at any time, and the counsellor will immediately lose access.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">4. Your Rights</h2>
          <p>You have the right to access, correct, and delete your personal data at any time. Use the "Delete my account and data" option in Account Settings for a complete data erasure. All deletions are immediate and irreversible.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">5. Data Retention</h2>
          <p>We retain your data only as long as your account is active. Upon deletion, all personal data is permanently removed from our systems within 24 hours.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">6. Contact</h2>
          <p>For privacy inquiries, contact us at privacy@careercompass.example.com</p>
        </section>
      </div>

      <div className="mt-10">
        <Link to="/" className="btn-secondary">← Back to Home</Link>
      </div>
    </div>
  );
}

export function DisclaimerPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
      <h1 className="text-3xl font-bold text-white mb-2">Disclaimer</h1>
      <p className="text-slate-500 text-sm mb-8">Last updated: October 2026</p>

      <div className="card border-yellow-700/30 bg-yellow-900/10 mb-8">
        <h2 className="text-lg font-bold text-yellow-300 mb-2">⚠️ Guidance Only — Not Professional Advice</h2>
        <p className="text-sm text-slate-300">
          CareerCompass is an <strong>educational tool</strong> designed to help students explore career options.
          It does <strong>not</strong> constitute professional career counselling, psychological assessment, or
          academic advising.
        </p>
      </div>

      <div className="space-y-6 text-slate-300 text-sm leading-relaxed">
        <section>
          <h3 className="font-semibold text-white mb-2">No Guarantee of Accuracy</h3>
          <p>Career recommendations are generated algorithmically based on self-reported data. The system cannot account for all individual circumstances, market conditions, or life factors. Results may not reflect actual career suitability.</p>
        </section>

        <section>
          <h3 className="font-semibold text-white mb-2">Consult a Professional</h3>
          <p>Before making significant academic or career decisions, you should consult with a qualified career counsellor, academic advisor, or relevant industry professional. Our in-app booking feature connects you with counsellors who can provide personalised guidance.</p>
        </section>

        <section>
          <h3 className="font-semibold text-white mb-2">RIASEC Assessment Limitations</h3>
          <p>The RIASEC (Holland Code) framework is a widely used vocational interest model, but it is one of many career assessment approaches. It is not a diagnostic tool and should not be used to make definitive conclusions about personality or capabilities.</p>
        </section>

        <section>
          <h3 className="font-semibold text-white mb-2">Not a Final Decision</h3>
          <p>Your results are a starting point for exploration, not a prescription. Career paths are complex and multifaceted — this tool is one input among many that should inform your decision-making process.</p>
        </section>

        <section>
          <h3 className="font-semibold text-white mb-2">Limitation of Liability</h3>
          <p>CareerCompass and its developers accept no liability for decisions made based on the platform's recommendations. All use of this platform is at your own risk.</p>
        </section>
      </div>

      <div className="mt-10">
        <Link to="/" className="btn-secondary">← Back to Home</Link>
      </div>
    </div>
  );
}
