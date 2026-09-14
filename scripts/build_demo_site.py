"""Build a public demo from packaged SYNTHETIC inputs only, with all exports."""

import argparse
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pathwaybridge.cli import create_demo
from pathwaybridge.core import analyze
from pathwaybridge.report import write_report
from pathwaybridge.viewer import REPORT_FILES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True, help="New build directory")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    manifest = create_demo(args.out / "synthetic-inputs")
    site = args.out / "site"
    write_report(analyze(manifest), site)
    with ZipFile(site / "pathwaybridge-demo.zip", "x", compression=ZIP_DEFLATED) as bundle:
        for name in sorted(REPORT_FILES):
            bundle.write(site / name, arcname=f"pathwaybridge-demo/{name}")
        bundle.writestr(
            "pathwaybridge-demo/README.txt",
            "PathwayBridge synthetic demo / 合成数据演示\n\n"
            "Extract the entire ZIP, then open report.html in your browser.\n"
            "Keep the companion files together for JSON/TSV downloads.\n"
            "先解压整个文件夹，再打开 report.html；请保留旁边的文件，以便导出数据。\n"
            "No server, Python installation, or Internet connection is required to read it.\n"
            "查看解压后的报告不需要安装 Python。所有示例值均为合成数据。\n"
            "To serve with an installed PathwayBridge: pathwaybridge serve --report <folder>\n",
        )
    shutil.copyfile(site / "report.html", site / "index.html")
    html = (site / "index.html").read_text(encoding="utf-8")
    banner = (
        '<div class="notice" style="margin:16px auto;max-width:1160px">'
        "<strong>合成数据演示 / Synthetic demo</strong> · "
        '<a href="pathwaybridge-demo.zip" download>下载完整报告 ZIP</a> · '
        '<a href="https://github.com/guatou904/pathwaybridge/blob/main/README.zh-CN.md">'
        "使用说明与本地分析</a><br>"
        "可以搜索、筛选和查看原始记录。分析自己的数据请在本地运行 PathwayBridge。"
        "</div>"
    )
    (site / "index.html").write_text(html.replace("<body>", "<body>" + banner, 1), encoding="utf-8")
    print(site)


if __name__ == "__main__":
    main()
