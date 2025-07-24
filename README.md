# Usage guide
The scenario is that Alice want to schedule a meeting time with Bob, and they both don't want to share they own time-schedule, not even a little.
And there's a mentor of these two: ZY, who want to solve this problem.
## As Alice
```bash
python gui.py
```
1. choose `Alice`
2. Input N, t1,t2,t3,... seperated by newline \
   eg. 
   ```text
   20
   1
   3
   4
   18
   ```
3. Press `Calc`
4. Copy the generated string `A1:xxxx` and sent it to Bob with your favor way.
5. waiting for Bob send you a string format with `B2:xxxx`
6. paste it and Press `Calc`
7. Copy the generated string `A2:xxxx` and sent it to ZY with your favor way.
8. waiting for Bob send you the index `j`, paste it and Press `Calc`
9. you will get the free time slot that both of you have common. 
10. Announce it to Bob and (optionally) ZY.

## As Bob
```bash
python gui.py
```
1. choose `Bob`
2. paste string `A1:xxxx` Alice sent to you and Press `Calc`
3. get your first result `B1:xxx` and sent it to ZY
4. Input your free time slot seperated by lines and press `Calc`
5. copy generate string `B2:xxx` and send it to Alice
6. waiting for ZY sent you a index `i`, paste it in and press `Calc`.
7. sent Alice your newly generated index `j`.

## As ZY
```bash
python gui.py
```
1. choose `ZY`
2. waiting for Bob sent you `B1:xxx`, paste it
3. waiting for Alice sent you `A2:xxx`, paste it
3. Press `Calc`, and send the generated index `i` to Bob.