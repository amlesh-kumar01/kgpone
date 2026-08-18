import re

path = 'src/pages/DocumentPipeline.jsx'
with open(path, 'r') as f:
    content = f.read()

# Replace hardcoded slate colors with semantic UI colors
replacements = {
    'text-slate-100': 'text-foreground',
    'text-slate-200': 'text-foreground',
    'text-slate-300': 'text-foreground/90',
    'text-slate-400': 'text-muted-foreground',
    'text-slate-500': 'text-muted-foreground',
    'text-slate-600': 'text-muted-foreground',
    'text-slate-900': 'text-background',
    'bg-slate-900': 'bg-background',
    'bg-slate-950': 'bg-background',
    'bg-slate-800': 'bg-card hover:bg-accent',
    'bg-slate-700': 'bg-muted',
    'border-slate-800': 'border-border',
    'border-slate-700': 'border-border/50',
    'bg-slate-900/50': 'bg-card/50',
    'custom-scrollbar': 'scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent'
}

for old, new in replacements.items():
    content = content.replace(old, new)

if 'doclingStyle' not in content:
    content = content.replace(
        "import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';",
        "import { vscDarkPlus as doclingStyle } from 'react-syntax-highlighter/dist/esm/styles/prism';"
    )
    content = content.replace(
        "style={vscDarkPlus}",
        "style={doclingStyle}"
    )

# Add a download button for JSON
# Find the CardHeader for JSON output
header_match = r'(<CardTitle className="text-lg font-medium text-amber-500 flex items-center">\s*<FileJson size=\{18\} className="mr-2" />\s*\{selectedStage\} Output\s*</CardTitle>)'
download_btn = r'''\1
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="mt-2 text-xs h-8 border-border hover:bg-accent"
                        disabled={!outputData}
                        onClick={() => {
                          if (!outputData) return;
                          const blob = new Blob([JSON.stringify(outputData, null, 2)], { type: 'application/json' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `${selectedStage.toLowerCase()}_output.json`;
                          a.click();
                          URL.revokeObjectURL(url);
                        }}
                      >
                        <Download size={14} className="mr-2" /> Download JSON
                      </Button>'''

content = re.sub(header_match, download_btn, content)

# Make markdown background visible and styled
content = content.replace('prose prose-invert prose-amber max-w-none', 'prose prose-sm md:prose-base dark:prose-invert prose-amber max-w-none bg-card p-6 rounded-lg border border-border shadow-sm')

with open(path, 'w') as f:
    f.write(content)

print('Updated UI styles for DocumentPipeline.jsx')
