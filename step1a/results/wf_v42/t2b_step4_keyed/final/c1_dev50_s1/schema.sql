CREATE TABLE "train_information" (
  "train id" INTEGER,
  "leave at" TIME,
  "requested people" INTEGER,
  "trainid" INTEGER,
  "price" NUMERIC(10, 2),
  "duration" INTERVAL,
  "departure" TEXT,
  "arrive by" TIME,
  "destination" TEXT,
  "confirmed reference" INTEGER,
  "day" TEXT,
  PRIMARY KEY ("train id"),
  FOREIGN KEY ("train id") REFERENCES "train_information" ("train id"),
  FOREIGN KEY ("trainid") REFERENCES "train_information" ("train id"),
  FOREIGN KEY ("confirmed reference") REFERENCES "train_information" ("train id"),
  FOREIGN KEY ("day") REFERENCES "train_information" ("train id")
);

CREATE TABLE "hotel_booking" (
  "hotel id" INTEGER,
  "postcode" INTEGER,
  "requested people" INTEGER,
  "type" TEXT,
  "stars" INTEGER,
  "requested day" TEXT,
  "price range" TEXT,
  "address" TEXT,
  "phone" INTEGER,
  "area" TEXT,
  "confirmed reference" INTEGER,
  "requested stay" INTEGER,
  PRIMARY KEY ("hotel id"),
  FOREIGN KEY ("hotel id") REFERENCES "hotel_booking" ("hotel id"),
  FOREIGN KEY ("confirmed reference") REFERENCES "hotel_booking" ("hotel id")
);

CREATE TABLE "restaurant_reservation" (
  "restaurant id" INTEGER,
  "food" TEXT,
  "postcode" INTEGER,
  "phone" INTEGER,
  "area" TEXT,
  "requested time" TIME,
  "confirmed reference" INTEGER,
  "price range" TEXT,
  "requested day" TEXT,
  "requested people" INTEGER,
  "address" TEXT,
  "name" TEXT,
  PRIMARY KEY ("restaurant id"),
  FOREIGN KEY ("restaurant id") REFERENCES "restaurant_reservation" ("restaurant id"),
  FOREIGN KEY ("postcode") REFERENCES "restaurant_reservation" ("restaurant id"),
  FOREIGN KEY ("confirmed reference") REFERENCES "restaurant_reservation" ("restaurant id")
);
