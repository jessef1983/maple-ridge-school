# Gravely tractors

Two Gravely Professional 16-G riding tractors (built 1988–2001) and their attachments.

## Purchases

| Date | Item | Price | Notes |
|---|---|---|---|
| | 2× Gravely 16-G Pro, rough condition ([FB listing](https://www.facebook.com/share/1Dxrge12F6/)) | $1,000 | Includes snowblower, mowing deck, and a blade (blade is walk-behind series) |
| | Snow plow | $150 | |
| | Plow brackets + rear ATV tires ([FB seller](https://www.facebook.com/share/1BXruCeo3p/)) | $120 | |
| | *Pending:* 8000-series parts tractor (FB) | $50 | Clutch/drivetrain donor — confirm model # |

**Total so far:** $1,270

## Units

| Unit | Serial # | Second plate # | Engine | Condition / known issues | Photo |
|---|---|---|---|---|---|
| Tractor A | 00622799 | 47578 | | | [plate](tractor-a-sn-00622799.jpeg) |
| Tractor B | 00609830 | 45541 | | | [plate](tractor-b-sn-00609830.jpeg) |
| Parts unit (8000 series) | | | | | |

The second plate (Gravely, Clemmons NC) sits below the S/N plate and has a stamped 5-digit number. It probably isn't the model number: 16-G model numbers in owner posts are 6 digits starting with 987, like 987070 and 987061. The model # tag may be under the front hood, glued to the dash support ([TractorByNet](https://www.tractorbynet.com/forums/threads/gravely-pro-16-g-series.447115)). Look for it there, then give model # + serial # to a Gravely/Ariens dealer to get the build year.

## 8000-series parts compatibility

- The 8000 series was replaced by the Professional G series in 1987 ([Wikipedia](https://en.wikipedia.org/wiki/Gravely_Tractor)). Both use 8-forward/4-reverse gear transmissions ([16-G](https://www.tractordata.com/lawn-tractors/000/8/6/862-gravely-16-g-transmission.html), [8179](https://www.tractordata.com/lawn-tractors/000/8/5/852-gravely-8179-transmission.html)).
- Owners report that most 8000 parts other than the engine fit the G series. Parts sellers list a "new style" clutch for both late 8000s and G-series tractors.
- **Not confirmed:** whether the forward/reverse clutch is a direct swap. Get the parts unit's model #. Late 8000s (8163, 8171, 8179, 8183, 8199) are the most likely match. Compare part numbers on a parts diagram, or ask Hank.

See [hank-notes.md](hank-notes.md) for repair advice from Hank.

## Specs

- Stock rear tire: 23x8.50-12. Front: 16x6.50-8. ([TractorData](https://www.tractordata.com/lawn-tractors/000/8/6/862-gravely-16-g.html))
- Rear hub bolt pattern: *(measure)*
- Service manual: Professional-G Series, 26793B

## Attachments

| Attachment | Fits | Condition | Notes |
|---|---|---|---|
| Snowblower | 16-G | | |
| Mowing deck | 16-G | | |
| Blade | Walk-behind series | | Doesn't fit the 16-G as-is |
| Snow plow | | | |
| Plow brackets | | | |
| Rear ATV tires | | | Size? Do they fit the 12" stock rims? |

## Tires

| Position | Stock | Planned | Fits stock rim? |
|---|---|---|---|
| Rear | 23x8.50-12 | ATV tires on their own rims (from the FB seller above; size TBD) | Depends on the size. A 22x10-9 tire needs 9" wheels, so the hub bolt pattern must match |
| Front | 16x6.50-8 | Kenda AT 20x7-8 ([photo](front-tire-wanted-kenda-at20x7-8.jpg)) | **Yes on bead diameter.** Both are 8" |

Front-tire notes:
- The 20" tire is **4" taller** than the stock 16" one, so the front sits about 2" higher. Check that the tire clears the frame and hood at full steering lock, and check how the mower deck hangs.
- The 7" section is a little wider than the stock 6.50. That's normally OK on the stock rim, but measure the rim width between the beads.
- Combined with the 22" rears, the tractor sits nose-up compared with stock (16 front / 23 rear).

## Snow plow

Plow bought separately ($150). The brackets came from Brandon, the tire seller.

### Lift rod (to fab)
Reference: Brandon's other Gravely ([top pivot](plow-lift-rod-ref-top-pivot.jpg), [spring 1](plow-lift-rod-ref-spring-1.jpg), [spring 2](plow-lift-rod-ref-spring-2.jpg)).

What the photos show:
- A round rod hangs down from a frame bracket. Its top end is bolted through the bracket, so the rod can pivot.
- A long coil spring sits on the rod, with a stack of nuts/collars at the bottom end. The spring cushions the lift and lets the blade float a bit.

Hank's method: buy a 12" bolt, cut off the head, put a 90° bend in it, and drill a hole for a cotter pin (see [hank-notes.md](hank-notes.md)). This seems to be the same part as Brandon's rod, just a cheaper way to make it:
- **Bent end:** goes through the hole in the lift arm or bracket. The cotter pin through the drilled hole keeps it from sliding out. It replaces the bolted eye on Brandon's.
- **Threaded end:** this is why to start from a bolt. The spring slides on, and nuts and washers set the preload and length.
- Size the bolt to the bracket hole. A plain-steel (grade 2) bolt bends cold in a vise. Heat a grade 5 or 8 bolt before bending it, or it may crack.

**Top fitting (on hand):** a spring-sleeve quick-release ball joint ([assembled](plow-lift-ball-joint-assembled.jpg), [apart](plow-lift-ball-joint-apart.jpg)).
- The ball stud bolts to the lift arm. To release it, pull the sleeve back against the spring.
- The socket has a **1/2-20 (fine) female thread**, and the rod screws into it.

**Rod layout:**
- **Top:** the 1/2-20 threaded end goes into the ball-joint socket, locked with a jam nut.
- **Bottom:** a 90° bend in the plain shank where the head was cut off. It goes through the plow bracket, held by a cotter pin.

**Rod stock:**
- 1/2-20 bolts are mostly grade 5 or 8, so heat the shank before bending.
- Or use 1/2" round bar, with a 1/2-20 thread cut on one end with a die.

**Ball size: mismatched.** The socket cavity is considerably larger than the ball ([photo](plow-lift-ball-vs-socket.jpg)), and the top of the ball looks flattened. Either the ball is worn or it's the wrong stud. **Don't reuse it.** It could pop out under load.
- [ ] Measure the socket's inside diameter (calipers, or the shank of a drill bit that just fits). Common sizes: 10, 13, 16 mm.
- [ ] Buy a ball stud of that ball diameter (McMaster or ag linkage suppliers), with a stud thread that fits the lift arm hole.
- Welding a ball onto a bolt is a fallback only. The ball must match the socket exactly and be centered, and hardened bearing balls weld poorly.

Measure on Brandon's tractor if you can. Otherwise measure your own lift arm and plow:
- [ ] Rod diameter and overall length
- [ ] Spring: free length, outside diameter, wire diameter
- [ ] What's in the bottom nut/collar stack, and the thread size
- [ ] Top connection: bolt-through eye or 90° bend? Bracket hole size?

### Angle lever
- [ ] Photograph the plow's pivot and angle plate to see whether it's a pull-pin through a hole quadrant or a different mechanism. Then decide whether to fab or buy.

## Seat

[Photo](seat-pan-and-cushion.jpg): a black plastic pan with a separate molded vinyl-over-foam cushion. The cushion skin is cracked and peeling. The pan is fine, but the threaded inserts are rusty.

- Gravely sells seat cushion parts, such as the [bottom cushion 21560800](https://www.gravely.com/en-us/part/21560800), the [cushion cover 21557800](https://www.gravely.com/en-us/part/21557800) and the [back cushion kit 59204300](https://www.gravely.com/en-us/part/59204300). None of them are confirmed to fit the 16-G. Check with a dealer using the model and serial numbers.
- Fallbacks: have an upholstery shop recover the existing cushion, or bolt on a universal tractor seat. Measure the bolt spacing first.

## Decals / repaint

Plan: burn off and repaint the panels (see Paint in [hank-notes.md](hank-notes.md)).

- [Photo](decals-maintenance-and-12v-ground.jpg): the black "Maintenance Instructions" plate and the "12 Volt Negative Ground" decal. Photograph and measure every decal **before stripping** so they can be reproduced.
- I found no reproduction G-series decal set. Gravely has told owners it doesn't stock decals for older models ([forum](https://lawnmowerforum.com/threads/1998-gravely-decals-for-50-walk-behind.5651/exportthread)). Places to try:
  - A Gravely dealer, with the model and serial numbers. Safety decals are sometimes still available.
  - eBay sellers of vintage engine and tractor decals.
  - The Gravely Tractor Club of America.
  - A local sign shop, working from your photos and measurements.

## Open items

- [ ] Measure rear hub bolt pattern
- [ ] Confirm the 8000-series parts unit's model # matches the 16-G's clutch/transmission
- [ ] Rear tire/wheel plan

## Log

