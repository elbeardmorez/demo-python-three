from src.runner import runner
from src.exceptions import NonFatalException, FatalException
from src.utils import trace

if __name__ == "__main__":
    runner_ = runner()
    while True:
        try:
            results = runner_.run()
            l_results = len(results)
            if l_results > 0:
                trace(0, f"{l_results} sql injection vulnerabilit" +
                      f"{'y' if l_results == 1 else 'ies'} identified at:")
                print('\n'.join([str(result) for result in results]))
            else:
                trace(0, "no sql injection vulnerabilities identified")
            break
        except NonFatalException as e:
            trace(0, f"non-fatal error encountered..\n{e}\ncontinuing")
        except FatalException as e:
            print(e)
            exit(1)
        # except Exception as e:
        #     trace(-1, f"unhandled exception:\n{e._}")
        #     exit(1)
