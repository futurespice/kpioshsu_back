from docx import Document


def docx_to_markdown(docx_path, output_path):
    doc = Document(docx_path)
    lines = []

    for block in doc.element.body:
        tag = block.tag.split('}')[-1]

        if tag == 'p':
            # Параграф
            from docx.oxml.ns import qn
            style = block.find(f'.//{qn("w:pStyle")}')
            style_name = style.get(qn('w:val'), '') if style is not None else ''

            text = ''.join(r.text for r in block.iter()
                           if r.tag.split('}')[-1] == 't' and r.text)

            if not text.strip():
                lines.append('')
                continue

            if 'Heading1' in style_name or style_name == '1':
                lines.append(f'# {text}')
            elif 'Heading2' in style_name or style_name == '2':
                lines.append(f'## {text}')
            elif 'Heading3' in style_name or style_name == '3':
                lines.append(f'### {text}')
            else:
                lines.append(text)

        elif tag == 'tbl':
            # Таблица
            from docx.oxml.ns import qn
            rows = block.findall(f'.//{qn("w:tr")}')
            table_lines = []

            for i, row in enumerate(rows):
                cells = row.findall(f'.//{qn("w:tc")}')
                cell_texts = []
                for cell in cells:
                    text = ''.join(r.text for r in cell.iter()
                                   if r.tag.split('}')[-1] == 't' and r.text)
                    cell_texts.append(text.strip().replace('\n', ' '))

                table_lines.append('| ' + ' | '.join(cell_texts) + ' |')

                # Разделитель после первой строки
                if i == 0:
                    table_lines.append('| ' + ' | '.join(['---'] * len(cell_texts)) + ' |')

            lines.append('')
            lines.extend(table_lines)
            lines.append('')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Готово! Сохранено в {output_path}")


# Использование
docx_to_markdown('TZ_Backend_KPI_OSHSU_v2.docx', 'TZ_Backend_v2.md')
