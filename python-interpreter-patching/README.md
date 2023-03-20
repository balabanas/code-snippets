# Python Interpreter Patching Examples

The source code for Python 2.7 was used. The instructions that I referred to were very helpful, but not executed literally. Please see the final patches.

* `inc.patch` - implementation of the inplace increment (`++` operator). Followed [1] 
* `until.patch` - implementation of the `until` statement [2]
* `new_opcode.patch` - new opcode implementation and folding 2 existing opcodes to a new one [3]

`p.sh` - initial setup and pulling python repo

## References
1. [https://hackernoon.com/modifying-the-python-language-in-7-minutes-b94b0a99ce14](https://hackernoon.com/modifying-the-python-language-in-7-minutes-b94b0a99ce14)
2. [https://eli.thegreenplace.net/2010/06/30/python-internals-adding-a-new-statement-to-python/](https://eli.thegreenplace.net/2010/06/30/python-internals-adding-a-new-statement-to-python/)
3. [https://blog.quarkslab.com/building-an-obfuscated-python-interpreter-we-need-more-opcodes.html](https://blog.quarkslab.com/building-an-obfuscated-python-interpreter-we-need-more-opcodes.html)
4. How to make a patch: [https://www.devroom.io/2009/10/26/how-to-create-and-apply-a-patch-with-git/](https://www.devroom.io/2009/10/26/how-to-create-and-apply-a-patch-with-git/)

