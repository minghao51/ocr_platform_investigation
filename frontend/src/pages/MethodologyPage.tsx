

export default function MethodologyPage() {
    return (
        <div className="max-w-4xl mx-auto p-6 space-y-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-4">Extraction Methodologies</h1>
                <p className="text-lg text-gray-600">
                    Understanding the different extraction methods helps you get the best results. Our platform now features <strong>intelligent auto-detection</strong> that automatically selects the optimal pipeline for your documents.
                </p>
            </div>

            {/* Auto-Detection Banner */}
            <section className="bg-gradient-to-r from-purple-50 to-indigo-50 p-6 rounded-lg border border-purple-200">
                <div className="flex items-start">
                    <div className="flex-shrink-0">
                        <svg className="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <div className="ml-4">
                        <h3 className="text-lg font-semibold text-purple-800 mb-2">New: Smart Auto-Detection</h3>
                        <p className="text-purple-700 mb-2">
                            Our <strong>Smart Extraction</strong> automatically analyzes your document and chooses the best method:
                        </p>
                        <ul className="text-sm text-purple-700 space-y-1 ml-4">
                            <li>• <strong>Digital PDFs</strong> → Text Extraction (87x faster, 90% cheaper)</li>
                            <li>• <strong>Scanned docs</strong> → Vision Extraction (high accuracy)</li>
                            <li>• <strong>Mixed content</strong> → Hybrid Pipeline (balanced approach)</li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Comparison Table */}
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-800">Quick Comparison</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Feature</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-purple-600 uppercase tracking-wider">Smart Auto</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-blue-600 uppercase tracking-wider">Vision</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-green-600 uppercase tracking-wider">Text</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            <tr>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Technology</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Intelligent classifier + adaptive routing</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Vision Language Models (VLMs)</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Programmatic Parser (pdfplumber) + LLM</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">How it "reads"</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Analyzes document type first, then routes</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Visually (like a human eye)</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Raw text layer extraction</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Best for</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Mixed workloads (recommended default)</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Scanned docs, handwriting, complex layouts</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Digital PDFs, large text volumes</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Speed</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Adaptive: &lt;0.5s (digital) / 3-10s (scanned)</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Slower (3-10s avg)</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Fast (&lt;0.5s)</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Cost</td>
                                <td className="px-6 py-4 text-sm text-gray-500">60-90% savings vs. Vision-only</td>
                                <td className="px-6 py-4 text-sm text-gray-500">More expensive</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Cheapest (90% vs. Vision)</td>
                            </tr>
                            <tr>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Handling Images</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Routes to Vision when detected</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Native understanding</td>
                                <td className="px-6 py-4 text-sm text-gray-500">Ignored (cannot see images)</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            {/* Detailed Analysis */}
            <div className="grid md:grid-cols-2 gap-8">
                {/* Vision Section */}
                <section className="bg-white p-6 rounded-lg shadow-sm border border-blue-100">
                    <div className="flex items-center mb-4">
                        <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center mr-3">
                            <span className="text-blue-600 font-bold">V</span>
                        </div>
                        <h2 className="text-xl font-bold text-gray-900">Vision Extraction</h2>
                    </div>
                    <p className="text-gray-600 mb-4">
                        Uses generic Vision Language Models (like Gemini Pro Vision) to process the document as an image. This approach preserves the spatial relationship of elements.
                    </p>
                    <h3 className="font-semibold text-gray-800 mb-2">Pros:</h3>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1 mb-4">
                        <li>Understands complex layouts (tables, forms).</li>
                        <li>Reads handwriting and signatures.</li>
                        <li>Recognizes charts, diagrams, and images.</li>
                        <li>Works on scanned documents (images).</li>
                    </ul>
                    <h3 className="font-semibold text-gray-800 mb-2">Cons:</h3>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        <li>Higher latency and token cost.</li>
                        <li>Can sometimes hallucinate small text details.</li>
                    </ul>
                </section>

                {/* Text Section */}
                <section className="bg-white p-6 rounded-lg shadow-sm border border-green-100">
                    <div className="flex items-center mb-4">
                        <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center mr-3">
                            <span className="text-green-600 font-bold">T</span>
                        </div>
                        <h2 className="text-xl font-bold text-gray-900">Text Extraction</h2>
                    </div>
                    <p className="text-gray-600 mb-4">
                        Extracts the raw text layer from digital PDFs using libraries like `pdfplumber`, then feeds only the text to an LLM. Visual layout information is largely lost.
                    </p>
                    <h3 className="font-semibold text-gray-800 mb-2">Pros:</h3>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1 mb-4">
                        <li>Extremely fast and cost-effective.</li>
                        <li>100% accurate text content (no OCR errors).</li>
                        <li>Great for contracts, reports, and books.</li>
                    </ul>
                    <h3 className="font-semibold text-gray-800 mb-2">Cons:</h3>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        <li>Fails completely on scanned images.</li>
                        <li>Complex tables may get jumbled.</li>
                        <li>Cannot extract information from charts/images.</li>
                    </ul>
                </section>
            </div>

            {/* How Auto-Detection Works */}
            <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h2 className="text-xl font-bold text-gray-900 mb-4">How Smart Auto-Detection Works</h2>
                <div className="space-y-4">
                    <div className="flex items-start">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center mr-3">
                            <span className="text-purple-600 font-semibold text-sm">1</span>
                        </div>
                        <div>
                            <h3 className="font-semibold text-gray-800">Document Analysis (&lt;0.2s)</h3>
                            <p className="text-sm text-gray-600">
                                When you upload a PDF, our classifier instantly analyzes:
                            </p>
                            <ul className="text-sm text-gray-600 mt-2 ml-4 space-y-1">
                                <li>• Document type (digital vs. scanned vs. mixed)</li>
                                <li>• Text layer presence and quality</li>
                                <li>• Text density (characters per page)</li>
                                <li>• Layout complexity (tables, columns, images)</li>
                            </ul>
                        </div>
                    </div>

                    <div className="flex items-start">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center mr-3">
                            <span className="text-purple-600 font-semibold text-sm">2</span>
                        </div>
                        <div>
                            <h3 className="font-semibold text-gray-800">Intelligent Routing</h3>
                            <p className="text-sm text-gray-600">
                                Based on the analysis, documents are routed to the optimal pipeline:
                            </p>
                            <div className="mt-3 grid md:grid-cols-3 gap-4">
                                <div className="bg-green-50 p-3 rounded border border-green-200">
                                    <h4 className="font-semibold text-green-800 text-sm mb-1">Text Pipeline</h4>
                                    <p className="text-xs text-green-700">Digital PDFs with extractable text</p>
                                </div>
                                <div className="bg-blue-50 p-3 rounded border border-blue-200">
                                    <h4 className="font-semibold text-blue-800 text-sm mb-1">Vision Pipeline</h4>
                                    <p className="text-xs text-blue-700">Scanned docs, images, complex layouts</p>
                                </div>
                                <div className="bg-orange-50 p-3 rounded border border-orange-200">
                                    <h4 className="font-semibold text-orange-800 text-sm mb-1">Hybrid Pipeline</h4>
                                    <p className="text-xs text-orange-700">Mixed content (coming soon)</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-start">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center mr-3">
                            <span className="text-purple-600 font-semibold text-sm">3</span>
                        </div>
                        <div>
                            <h3 className="font-semibold text-gray-800">Processing & Results</h3>
                            <p className="text-sm text-gray-600">
                                The selected pipeline processes your document and returns structured data.
                                You can see which method was used in the results display.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Technical Details */}
            <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Technical Details: PyMuPDF Document Classifier</h2>
                <div className="space-y-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                        <h3 className="font-semibold text-gray-800 mb-2">🚀 Ultra-Fast Classification Technology</h3>
                        <p className="text-sm text-gray-600 mb-3">
                            Our document classifier uses <strong>PyMuPDF (fitz)</strong>, a high-performance PDF library
                            that can analyze documents in <strong>&lt;0.15 seconds per page</strong>.
                        </p>
                        <div className="grid md:grid-cols-2 gap-4 text-sm">
                            <div>
                                <h4 className="font-medium text-gray-700 mb-1">What We Analyze:</h4>
                                <ul className="text-gray-600 space-y-1 ml-4">
                                    <li>• <strong>Text Layer Presence</strong> — Checks if PDF has extractable text</li>
                                    <li>• <strong>Text Density</strong> — Characters per page (threshold: 200+)</li>
                                    <li>• <strong>Document Type</strong> — Digital vs. Scanned vs. Mixed</li>
                                    <li>• <strong>Layout Complexity</strong> — Tables, columns, images (0-100 score)</li>
                                </ul>
                            </div>
                            <div>
                                <h4 className="font-medium text-gray-700 mb-1">Classification Rules:</h4>
                                <ul className="text-gray-600 space-y-1 ml-4">
                                    <li>• <strong>Digital + High Text Density</strong> → Text Pipeline</li>
                                    <li>• <strong>Scanned/No Text Layer</strong> → Vision Pipeline</li>
                                    <li>• <strong>Mixed Content</strong> → Hybrid Pipeline (coming soon)</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                        <h3 className="font-semibold text-purple-800 mb-2">⚡ Performance Comparison</h3>
                        <div className="overflow-x-auto">
                            <table className="min-w-full text-sm">
                                <thead>
                                    <tr className="border-b border-purple-200">
                                        <th className="text-left py-2 text-purple-900">Metric</th>
                                        <th className="text-left py-2 text-purple-900">Old (VLM Only)</th>
                                        <th className="text-left py-2 text-purple-900">New (Auto-Routed)</th>
                                        <th className="text-left py-2 text-purple-900">Improvement</th>
                                    </tr>
                                </thead>
                                <tbody className="text-gray-700">
                                    <tr className="border-b border-purple-100">
                                        <td className="py-2">Speed (Digital PDFs)</td>
                                        <td className="py-2">3-10s</td>
                                        <td className="py-2 font-semibold text-green-700">&lt;0.5s</td>
                                        <td className="py-2 font-semibold text-purple-700">87x faster</td>
                                    </tr>
                                    <tr className="border-b border-purple-100">
                                        <td className="py-2">Cost (per 1K pages)</td>
                                        <td className="py-2">$100-500</td>
                                        <td className="py-2 font-semibold text-green-700">$5-20</td>
                                        <td className="py-2 font-semibold text-purple-700">90% cheaper</td>
                                    </tr>
                                    <tr>
                                        <td className="py-2">Accuracy</td>
                                        <td className="py-2">95%+</td>
                                        <td className="py-2 font-semibold text-green-700">95-98%</td>
                                        <td className="py-2 font-semibold text-purple-700">Maintained</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                        <h3 className="font-semibold text-blue-800 mb-2">🔧 Pipeline Details</h3>
                        <div className="grid md:grid-cols-3 gap-4 text-sm">
                            <div>
                                <h4 className="font-medium text-blue-900 mb-1">Text Pipeline</h4>
                                <ul className="text-blue-700 space-y-1">
                                    <li>• <strong>Tool:</strong> pdfplumber</li>
                                    <li>• <strong>Speed:</strong> &lt;0.5s</li>
                                    <li>• <strong>Accuracy:</strong> 95-98%</li>
                                    <li>• <strong>Best:</strong> Digital PDFs</li>
                                </ul>
                            </div>
                            <div>
                                <h4 className="font-medium text-blue-900 mb-1">Vision Pipeline</h4>
                                <ul className="text-blue-700 space-y-1">
                                    <li>• <strong>Tool:</strong> VLMs (Gemini, etc.)</li>
                                    <li>• <strong>Speed:</strong> 3-10s</li>
                                    <li>• <strong>Accuracy:</strong> 95%+</li>
                                    <li>• <strong>Best:</strong> Scanned docs</li>
                                </ul>
                            </div>
                            <div>
                                <h4 className="font-medium text-blue-900 mb-1">Hybrid Pipeline</h4>
                                <ul className="text-blue-700 space-y-1">
                                    <li>• <strong>Tool:</strong> PaddleOCR + VLM</li>
                                    <li>• <strong>Speed:</strong> 1-3s</li>
                                    <li>• <strong>Accuracy:</strong> 96-98%</li>
                                    <li>• <strong>Best:</strong> Mixed content</li>
                                    <li className="text-xs italic text-blue-600">*Coming soon</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Updated Recommendation */}
            <section className="bg-gradient-to-r from-purple-50 to-indigo-50 p-6 rounded-lg border border-purple-200">
                <h3 className="text-lg font-semibold text-purple-800 mb-3">Recommendation</h3>
                <div className="space-y-3">
                    <p className="text-purple-700">
                        <strong>✓ Use Smart Auto-Detection (Recommended)</strong><br />
                        <span className="text-sm">Best choice for most users. Automatically optimizes for speed, cost, and accuracy.</span>
                    </p>
                    <p className="text-purple-700">
                        <strong>Manual Selection (Advanced Users)</strong><br />
                        <span className="text-sm">
                            • <strong>Vision Extraction</strong> — Scanned documents, handwritten forms, image-only PDFs<br />
                            • <strong>Text Extraction</strong> — Known digital PDFs (e.g., invoices exported from accounting software)
                        </span>
                    </p>
                </div>
            </section>
        </div>
    );
}
