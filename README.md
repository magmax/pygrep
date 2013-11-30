
Pygrep is a graphical tool similar to **GNU "grep"**.

Usually, when you are developping a big application, you must battle with a lot of sources, and you need to search a lot of words (variables, function names, constants and so on). A lot of times, _"grep"_ is powerful enougth to help you in your searchs, but other times it is not.

This program tries to help you in these cases:

- It will allow to save a **profile** with different configurations of search directories.
- You'll be able to click on the found labels and open the file on your default (or not) **editor**.
- You can decide if you want to search only in the files that was obtained in the last search. Notice that it is not the same as `$ grep word|grep word2`, but may be similar to `$ grep word2 $(grep -H word|cut -f1 -d':')`
- It will be possible to show the line before/after/both the expresion to search (the match expresion will be highlighted)
- Well... I have no more requisites, but when people will use it, they could give their experiences.
