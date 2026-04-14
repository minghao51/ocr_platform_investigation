import { Link } from 'react-router-dom';

interface LandingPageProps {
  isAuthenticated: boolean;
  username?: string;
}

const features = [
  {
    title: 'Smart Extraction',
    description: 'Auto-route documents to the best extraction pipeline for speed, accuracy, and cost efficiency.',
    accent: 'blue',
  },
  {
    title: 'Structured Output',
    description: 'Define custom schemas and extract consistent JSON-ready data from invoices, forms, and reports.',
    accent: 'emerald',
  },
  {
    title: 'Processing History',
    description: 'Review previous jobs, inspect outputs, and manage OCR results from one place.',
    accent: 'slate',
  },
];

const accentClasses: Record<string, string> = {
  blue: 'border-blue-200 bg-blue-50 text-blue-700',
  emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  slate: 'border-gray-200 bg-gray-50 text-gray-700',
};

export default function LandingPage({ isAuthenticated, username }: LandingPageProps) {
  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
      <section className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        <div className="px-8 py-10 bg-gradient-to-r from-blue-50 via-white to-indigo-50">
          <div className="max-w-3xl">
            <div className="inline-flex items-center rounded-full border border-blue-200 bg-white px-3 py-1 text-xs font-medium text-blue-700 mb-4">
              OCR Platform
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 tracking-tight">
              Extract structured data from documents with a simple, guided workflow
            </h1>
            <p className="mt-4 text-base text-gray-600">
              Upload files, choose a model, define your schema, and process with smart routing that adapts to digital and scanned documents.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                to="/extract"
                className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                Start Extraction
              </Link>
              <Link
                to="/methodology"
                className="px-4 py-2 rounded-md border border-gray-300 bg-white text-gray-700 text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                Learn Methodology
              </Link>
              <Link
                to="/history"
                className="px-4 py-2 rounded-md border border-gray-300 bg-white text-gray-700 text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                View History
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {features.map((feature) => (
          <div key={feature.title} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${accentClasses[feature.accent]}`}>
              {feature.title}
            </div>
            <p className="mt-4 text-sm leading-6 text-gray-600">{feature.description}</p>
          </div>
        ))}
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900">How it works</h2>
          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            {[
              ['1', 'Upload', 'PDFs and images are supported.'],
              ['2', 'Configure', 'Select model + schema for your extraction target.'],
              ['3', 'Process', 'Track status and inspect structured results.'],
            ].map(([step, title, desc]) => (
              <div key={step} className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 text-sm font-semibold flex items-center justify-center">
                  {step}
                </div>
                <h3 className="mt-3 text-sm font-semibold text-gray-900">{title}</h3>
                <p className="mt-1 text-sm text-gray-600">{desc}</p>
              </div>
            ))}
          </div>
        </div>

        <aside className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">Workspace status</h2>
          <p className="mt-3 text-sm text-gray-600">
            {isAuthenticated
              ? `Signed in${username ? ` as ${username}` : ''}. You can upload documents, process OCR jobs, and review history.`
              : 'Guest mode is active. You can explore the app now, then sign in from the top-right menu when you want to upload documents or open history.'}
          </p>
          <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Recommended next step</p>
            <p className="mt-1 text-sm text-gray-700">
              Open <span className="font-medium">Extract</span> to run a document through the smart extraction pipeline.
            </p>
          </div>
        </aside>
      </section>
    </div>
  );
}
