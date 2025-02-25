import sys, re


def converter(filename):
    header = r"^(#{1,6}) +"
    italic = r"\*(.*?)\*"
    bold = r"\*\*(.*?)\*\*(?!\*)"
    num_list = r"^(\d). +(.*)"
    limit_list = False
    url_link = r"\[(.*?)\]\((.*?)\)"
    image_link = r"!\[(.*?)]?\((.*?)\)"

    with open(filename, "r", encoding="utf-8") as file:
        html = ""
        text = file.read()
        lines = text.split("\n")
    
        for line in lines:
            # Header
            found = re.search(header, line)
            if found:
                num = len(found.group()) - 1
                if 1 <= num <= 6:
                    line = line.replace(found.group(), f"<h{num}>")
                    line += (f"</h{num}>")

            # Bold, Italic, Links
            line = re.sub(bold, r"<b>\1</b>", line)
            line = re.sub(italic, r"<i>\1</i>", line)
            line = re.sub(image_link, r'<img src="\2" alt=\1"/>', line)
            line = re.sub(url_link, r'<a href="\2">\1</a>', line)

            # Ordered List
            found = re.search(num_list, line)
            if found:
                limit_list = True
                if (int(found.group(1)) == 1):
                    html += "<ol>\n"
                    html += f"<li>{found.group(2)}</li>\n"
                else:
                    html += f"<li>{found.group(2)}</li>\n"
                continue
            if not found and limit_list:
                html += "</ol>\n"
                limit_list = False

            html += line + "\n"

        return html


def main(file):
    html = converter(file)
    print("Texto convertido:")
    print(html)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Insufficient arguments. Usage: python3 converter.py <file>")
