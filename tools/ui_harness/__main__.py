import sys

if sys.argv[1:2] == ["menus"]:
    from tools.ui_harness.menus import main
    sys.exit(main(sys.argv[2:]))
from tools.ui_harness.harness import main
sys.exit(main())
