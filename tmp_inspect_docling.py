import inspect
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions
print('DocumentConverter init signature:', inspect.signature(DocumentConverter.__init__))
print('PdfPipelineOptions signature:', inspect.signature(PdfPipelineOptions))
print('AcceleratorOptions signature:', inspect.signature(AcceleratorOptions))
print('PdfPipelineOptions attrs:', [a for a in dir(PdfPipelineOptions) if not a.startswith('_')][:80])
