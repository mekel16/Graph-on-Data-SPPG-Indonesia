import requests


API_URL = "http://127.0.0.1:8010/ask"


def main():
    print("===================================")
    print("SPPG GraphRAG Terminal Chat")
    print("Ketik 'exit' atau 'quit' untuk keluar")
    print("===================================")

    while True:
        try:
            question = input("\nAnda: ").strip()

            if not question:
                continue

            if question.lower() in ["exit", "quit", "keluar"]:
                print("Sampai jumpa.")
                break

            response = requests.post(
                API_URL,
                json={
                    "question": question,
                },
                timeout=120,
            )

            if response.status_code != 200:
                print(
                    f"\nError HTTP {response.status_code}:"
                )
                print(response.text)
                continue

            data = response.json()

            print("\nAI:")
            print(data.get("answer", "Tidak ada jawaban."))

            print("\nIntent:")
            print(data.get("intent"))

        except requests.exceptions.ConnectionError:
            print(
                "\nTidak dapat terhubung ke FastAPI. "
                "Pastikan server sedang berjalan."
            )

        except requests.exceptions.Timeout:
            print(
                "\nRequest terlalu lama. "
                "Coba ulangi pertanyaannya."
            )

        except KeyboardInterrupt:
            print("\nProgram dihentikan.")
            break

        except Exception as error:
            print(f"\nError: {error}")


if __name__ == "__main__":
    main()