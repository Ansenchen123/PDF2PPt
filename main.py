import argparse
from pathlib import Path

from pdf2ppt.pipeline import convert_pdf_to_ppt as _convert_pdf_to_ppt


def convert_pdf_to_ppt(
    pdf_path: str,
    output_ppt: str,
    api_key: str | None = None,
    provider_name: str = "gemini",
    provider_model: str | None = None,
    auth_mode: str = "byok",
    proxy_url: str | None = None,
    proxy_token: str | None = None,
    start_page: int = 1,
    end_page: int | None = None,
    callback=None,
    keep_temp: bool = False,
):
    provider_adapter = "proxy" if auth_mode == "proxy" else provider_name
    return _convert_pdf_to_ppt(
        pdf_path=pdf_path,
        output_ppt=output_ppt,
        provider_name=provider_adapter,
        target_provider=provider_name,
        provider_model=provider_model,
        api_key=api_key,
        proxy_url=proxy_url,
        proxy_token=proxy_token,
        start_page=start_page,
        end_page=end_page,
        callback=callback,
        keep_temp=keep_temp,
    )

def main():
    parser = argparse.ArgumentParser(description="Convert PDF slides into editable PowerPoint decks.")
    parser.add_argument("pdf_path", help="Path to the input PDF file.")
    parser.add_argument("--output", default="output.pptx", help="Path to the output PPTX file.")
    parser.add_argument("--start-page", type=int, default=1, help="First page to process (1-based).")
    parser.add_argument("--end-page", type=int, help="Last page to process (1-based, inclusive).")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary page images for debugging.")
    parser.add_argument(
        "--provider",
        default="gemini",
        choices=["gemini", "openai", "anthropic", "mistral", "mock"],
        help="Layout extraction provider.",
    )
    parser.add_argument("--model", help="Provider model override.")
    parser.add_argument("--api-key", help="Provider API key override. Defaults to keyring or .env.")
    parser.add_argument("--auth-mode", choices=["byok", "proxy"], default="byok", help="Use local key or managed proxy.")
    parser.add_argument("--proxy-url", help="Managed proxy URL.")
    parser.add_argument("--proxy-token", help="Managed proxy bearer token.")
    
    args = parser.parse_args()
    
    try:
        convert_pdf_to_ppt(
            args.pdf_path,
            args.output,
            api_key=args.api_key,
            provider_name=args.provider,
            provider_model=args.model,
            auth_mode=args.auth_mode,
            proxy_url=args.proxy_url,
            proxy_token=args.proxy_token,
            start_page=args.start_page,
            end_page=args.end_page,
            keep_temp=args.keep_temp,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
