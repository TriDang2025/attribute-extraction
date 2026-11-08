CREATE TABLE "train" (
  "departure" TEXT,
  "destination" TEXT,
  "duration" INTERVAL,
  "price" NUMERIC(10, 2),
  "trainid" INTEGER,
  PRIMARY KEY ("trainid")
);

CREATE TABLE "train_booking" (
  "arrive by" TIME,
  "confirmed reference" INTEGER,
  "day" TEXT,
  "leave at" TIME,
  "requested people" INTEGER,
  "trainid" INTEGER,
  PRIMARY KEY ("confirmed reference"),
  FOREIGN KEY ("trainid") REFERENCES "train" ("trainid")
);

CREATE TABLE "hotel" (
  "address" TEXT,
  "area" TEXT,
  "internet" BOOLEAN,
  "name" TEXT,
  "parking" BOOLEAN,
  "phone" TEXT,
  "postcode" INTEGER,
  "price range" TEXT,
  "stars" INTEGER,
  "type" TEXT,
  PRIMARY KEY ("name")
);

CREATE TABLE "hotel_booking" (
  "confirmed reference" INTEGER,
  "requested day" TEXT,
  "requested people" INTEGER,
  "requested stay" INTEGER,
  "hotel name" TEXT,
  PRIMARY KEY ("confirmed reference"),
  FOREIGN KEY ("hotel name") REFERENCES "hotel" ("name")
);

CREATE TABLE "restaurant" (
  "address" TEXT,
  "area" TEXT,
  "food" TEXT,
  "name" TEXT,
  "phone" TEXT,
  "postcode" INTEGER,
  "price range" TEXT,
  PRIMARY KEY ("name")
);

CREATE TABLE "restaurant_booking" (
  "confirmed reference" INTEGER,
  "requested day" TEXT,
  "requested people" INTEGER,
  "requested time" TIME,
  "restaurant name" TEXT,
  PRIMARY KEY ("confirmed reference"),
  FOREIGN KEY ("restaurant name") REFERENCES "restaurant" ("name")
);
