CREATE TABLE "train_booking" (
  "train_booking id" INTEGER,
  "arrive by" TIME,
  "train day" TEXT,
  "train departure" TEXT,
  "train destination" TEXT,
  "train duration" INTERVAL,
  "train leave at" TIME,
  "train price" NUMERIC(10, 2),
  "train requested people" INTEGER,
  "Hotel requested day" TEXT,
  "Hotel requested people" INTEGER,
  "Hotel requested stay" INTEGER,
  "Hotel stars" INTEGER,
  "Restaurant requested day" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant requested time" TIME,
  PRIMARY KEY ("train_booking id")
);

CREATE TABLE "hotel_info" (
  "hotel id" INTEGER,
  "hotel address" TEXT,
  "hotel area" TEXT,
  "hotel name" TEXT,
  "hotel phone" INTEGER,
  "hotel price range" TEXT,
  "hotel type" TEXT,
  PRIMARY KEY ("hotel id")
);

CREATE TABLE "restaurant_info" (
  "restaurant id" INTEGER,
  "restaurant address" TEXT,
  "restaurant area" TEXT,
  "restaurant food" TEXT,
  "restaurant name" TEXT,
  "restaurant phone" INTEGER,
  "restaurant price range" TEXT,
  PRIMARY KEY ("restaurant id")
);

CREATE TABLE "bookings" (
  "booking id" INTEGER,
  "train confirmed reference" INTEGER,
  "hotel confirmed reference" INTEGER,
  "restaurant confirmed reference" INTEGER,
  "Train trainid" INTEGER,
  "Hotel postcode" INTEGER,
  "Restaurant postcode" INTEGER,
  PRIMARY KEY ("booking id"),
  FOREIGN KEY ("train confirmed reference") REFERENCES "train_booking" ("train_booking id"),
  FOREIGN KEY ("hotel confirmed reference") REFERENCES "hotel_info" ("hotel id"),
  FOREIGN KEY ("restaurant confirmed reference") REFERENCES "restaurant_info" ("restaurant id")
);
