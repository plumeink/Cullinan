# Documentation Organization

## Language Structure

Cullinan documentation is available in multiple languages:

```
docs/
├── README.md                    # Main index with language switcher
├── en/                          # English documentation (default)
│   ├── README.md
│   ├── 00-complete-guide.md
│   ├── 01-configuration.md
│   ├── 02-packaging.md
│   ├── 03-troubleshooting.md
│   ├── 04-quick-reference.md
│   ├── 05-build-scripts.md
│   └── 06-sys-path-auto-handling.md
└── zh/                          # Chinese documentation (中文文档)
    ├── README_zh.md
    ├── 00-complete-guide_zh.md
    ├── 01-configuration_zh.md
    ├── 02-packaging_zh.md
    ├── 03-troubleshooting_zh.md
    ├── 04-quick-reference_zh.md
    ├── 05-build-scripts_zh.md
    └── 06-sys-path-auto-handling_zh.md
```

## Language Switching

Each documentation file includes a language switcher at the top:

```markdown
[English](../en/filename.md) | [中文](../zh/filename_zh.md)
```

## Default Language

- **Default**: English (`en/`)
- **Alternative**: Chinese (`zh/`)

## Adding a New Language

1. Create a new language directory: `docs/{lang_code}/`
2. Copy and translate all files from `docs/en/`
3. Add language switcher links to all files
4. Update main `docs/README.md` to include the new language

## File Naming Convention

- **English**: `filename.md`
- **Chinese**: `filename_zh.md`
- **Other languages**: `filename_{lang_code}.md`

Example:
- `00-complete-guide.md` (English)
- `00-complete-guide_zh.md` (Chinese)
- `00-complete-guide_ja.md` (Japanese, if added)

## Maintenance

When updating documentation:

1. Update the English version first (`en/`)
2. Translate changes to all other language versions
3. Keep the structure and numbering consistent across languages
4. Ensure all internal links work in each language version

