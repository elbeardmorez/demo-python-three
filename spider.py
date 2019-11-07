from src.runner import runner
from src.exceptions import NonFatalException, FatalException
from src.utils import trace

if __name__ == "__main__":
    runner_ = runner()
    while True:
        try:
            runner_.run()
            break
        except NonFatalException as e:
            trace(0, f"non-fatal error encountered..\n{e}\ncontinuing")
        except FatalException as e:
            print(e)
            exit(1)
        # except Exception as e:
        #     trace(-1, f"unhandled exception:\n{e._}")
        #     exit(1)
