"""Locked script. Each line: (section, display_text, cue or None, pause_before, pause_after)."""
S = []
def L(sec, text, cue=None, pb=0.0, pa=0.0): S.append(dict(section=sec, text=text, cue=cue, pb=pb, pa=pa))

# 0:00 cold open
L("cold", "On one coding test, OpenAI's cheaper model came within half a point of its flagship.", "gap", 0.35)
L("cold", "And it cost about a fifth as much on that test.", "cost", 0.45)
L("cold", "So when would you actually need Astra?", "ask", 0.2, 0.7)
# launch
L("launch", "On November 17th, OpenAI released two models under one name: GPT-6.2.", "launch")
L("launch", "Astra is the flagship.", "astra", 0.2)
L("launch", "OpenAI pitches it at the hardest projects, the long, messy work where one wrong assumption can cost you an afternoon.")
L("launch", "Sol is the efficient one, built for everyday work.", "sol", 0.2)
L("launch", "And the price gap is real.", "price0")
L("launch", "In the API, Astra costs $8 per million input tokens, and $40 per million output.", "price", 0.3)
L("launch", "Sol is $2 and $10.", "pricesol", 0.15)
L("launch", "That's a quarter of the price, token for token.", "quarter", 0.15, 0.3)
L("launch", "So here's why each one matters.", "why")
L("launch", "If you run lots of routine jobs, Sol makes your budget go four times further.", "solwhy")
L("launch", "If you've got one job that has to be right, Astra is the one built to carry it.", "astrawhy", 0, 0.5)
# benchmark
L("bench", "Now, the result that caught my eye.", "bench")
L("bench", "FrontierCode 2.0 is a coding benchmark run by Cognition.", "fc")
L("bench", "It doesn't just check whether the code runs.", "runs")
L("bench", "It asks whether a project's maintainers would actually merge the change.", "merge")
L("bench", "That's a high bar, and it looks a lot like real work.")
L("bench", "Both models ran at max reasoning effort.", "max", 0, 0.2)
L("bench", "Astra scored 44.2.", "astrascore", 0.45)
L("bench", "Sol scored 43.8.", "solscore", 0.45)
L("bench", "That's a gap of 0.4 points.", "gapnum", 0.3, 0.8)
L("bench", "Now look at the bill.", "bill")
L("bench", "On this benchmark, Astra cost about $5.97 per task.", "astracost", 0.35)
L("bench", "Sol cost about $1.29.", "solcost", 0.4)
L("bench", "Roughly a fifth.", "fifth", 0.3, 0.8)
L("bench", "Here's how OpenAI sums it up.", "source")
L("bench", "Sol comes within half a point of Astra, at about one-fifth the cost, with both at max.", "quote", 0, 0.4)
L("bench", "Two caveats.", "caveat")
L("bench", "These are OpenAI-reported numbers, from one benchmark.", "cav1")
L("bench", "And that cost is per task on this test, not a quote for your workload.", "cav2", 0, 0.4)
L("bench", "But it does tell you something useful.", "takeaway")
L("bench", "On well-defined coding changes, the flagship isn't buying you much.", "takeaway2")
L("bench", "So where does the gap show up?", "where", 0, 0.6)
# website
L("web", "Scene one. A small bakery needs a landing page.", "web")
L("web", "Hero image, menu, opening hours, a contact form.", "webparts")
L("web", "You've got a wireframe, and that's exactly the kind of job FrontierCode rewards: a clear spec, a few files, and an easy way to check the result.", "wire")
L("web", "Then the complication.", "webcomp", 0.2)
L("web", "The owner wants it to work on phones, load fast, and send form messages straight to their inbox.", "mobile")
L("web", "And after the first draft, they'll want three rounds of changes.", "rounds")
L("web", "That's more work, but it's still well-defined work.")
L("web", "If the layout breaks, you see it. If the form fails, you know in seconds.", "webcheck")
L("web", "My pick here is Sol.", "webpick", 0.3, 0.2)
L("web", "When a mistake is cheap to spot and cheap to fix, you don't need the flagship.")
L("web", "At that benchmark's cost ratio, you could run about five Sol passes for the price of one Astra pass.", "passes", 0, 0.6)
# bug
L("bug", "Scene two is a different animal.", "bug")
L("bug", "Checkout totals are off by a cent, but only sometimes.", "cent")
L("bug", "The error shows up on the receipt, but the cause isn't there.", "trace")
L("bug", "It runs back through the cart, a currency helper, and a discount rule someone changed months ago.", "chain")
L("bug", "You can only reproduce it with the right coupon, in the right currency.", "coupon")
L("bug", "Here's the complication: every file looks fine on its own.", "bugcomp", 0.2)
L("bug", "The bug is in how they connect.", "connect")
L("bug", "And a wrong fix doesn't fail loudly. It ships, and quietly charges the wrong amount.", "wrongfix")
L("bug", "This is where I'd reach for Astra.", "bugpick", 0.3, 0.2)
L("bug", "Not because Sol can't read code, but because a confident wrong answer costs more than the price difference.")
L("bug", "Let Sol reproduce the bug and add logging. Then hand the fix to Astra.", "handoff", 0, 0.6)
# slides
L("slides", "Scene three. You've got rough meeting notes, and you need a ten-slide deck by tomorrow.", "slides")
L("slides", "Fragments, a few numbers, half an idea for a chart.", "frag")
L("slides", "For an internal update, Sol is fine.", "slidesol", 0.2)
L("slides", "It'll turn the notes into an outline, headlines and speaker notes, and you'll tidy the rest in a few minutes.", "outline")
L("slides", "Now change the job.", "slidecomp", 0.3, 0.2)
L("slides", "The deck has to follow a strict brand template: fixed fonts, locked layouts, a legal footer on every slide.", "template")
L("slides", "And the source isn't notes anymore. It's a forty-page report and a spreadsheet, and every figure has to match.", "source2")
L("slides", "Now, one wrong number in front of a client is the expensive mistake.", "wrongnum")
L("slides", "That's when I'd switch to Astra.", "slidepick", 0.3)
L("slides", "Same kind of task. Different stakes.", "stakes", 0, 0.7)
# verdict
L("verdict", "So here's the verdict.", "verdict")
L("verdict", "Under Sol: the bakery site, the internal deck, and most routine code changes.", "vsol")
L("verdict", "It came within half a point on that coding test, at a fraction of the cost.")
L("verdict", "Under Astra: the cross-file money bug, and the client deck with a strict template.", "vastra", 0.2)
L("verdict", "And the switch rule is simple.", "rule", 0.3)
L("verdict", "Start with Sol.", "r1", 0.1)
L("verdict", "Move to Astra when the work spans lots of connected pieces, when you can't check the result quickly, or when one mistake costs more than the price gap.", "r2")
L("verdict", "If none of those are true, Sol is probably enough.", "r3")
L("verdict", "Sol is your default. Astra is your escalation.", "end", 0.3)

SAY = [  # spoken substitutions, applied in order
    ("GPT-6.2", "G.P.T. six point two"), ("November 17th", "November seventeenth"),
    ("FrontierCode 2.0", "Frontier Code two point oh"), ("FrontierCode", "Frontier Code"),
    ("$8 per", "eight dollars per"), ("$40 per", "forty dollars per"), ("$2 and $10", "two dollars and ten"),
    ("44.2", "forty-four point two"), ("43.8", "forty-three point eight"), ("0.4", "zero point four"),
    ("$5.97", "five dollars ninety-seven"), ("about $1.29", "about a dollar twenty-nine"),
    ("API", "A.P.I."),
]
import re as _re
def say(t):
    for a, b in SAY: t = t.replace(a, b)
    t = t.replace("OpenAI-reported", "OpenAI reported")
    return _re.sub(r"\bSol\b", "Soul", t)
