import sys, traceback
try:
    import main
    main.main()
except Exception as e:
    with open('C:\\Users\\cesar\\Desktop\\fatal_error.txt', 'w') as f:
        f.write(traceback.format_exc())
