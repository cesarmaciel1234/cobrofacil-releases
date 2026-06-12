import sys
import traceback

def custom_excepthook(exc_type, exc_value, exc_traceback):
    with open("detailed_crash.log", "w") as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = custom_excepthook

try:
    import main
    if hasattr(main, 'main'):
        main.main()
except Exception as e:
    with open("detailed_crash.log", "w") as f:
        traceback.print_exc(file=f)
