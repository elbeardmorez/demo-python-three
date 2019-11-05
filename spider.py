from src.runner import runner
from src.exceptions import NonFatalException, FatalException

if __name__ == "__main__":
    runner_ = runner()
    while True:
        try:
            results = runner_.run()
            l_results = len(results)
            if l_results > 0:
                print(f"# {l_results} sql injection vulnerabilit" +
                      f"{'y' if l_results == 1 else 'ies'} identified at:")
                print('\n'.join(results))
            else:
                print("no sql injection vulnerabilities identified")
            break
        except NonFatalException as e:
            print(f"[info] non-fatal error encountered..\n{e}\ncontinuing")
        except FatalException as e:
            print(e)
            exit(1)
        # except Exception as e:
        #     print(f"[error] unhandled exception:\n{e._}")
        #     exit(1)
