from src.runner import runner

if __name__ == "__main__":
    runner_ = runner()
    results = runner_.run()
    l_results = len(results)
    if l_results > 0:
        print(f"# {l_results} sql injection vulnerabilit" +
              f"{'y' if l_results == 1 else 'ies'} identified at:")
        print('\n'.join(results))
    else:
        print("no sql injection vulnerabilities identified")
