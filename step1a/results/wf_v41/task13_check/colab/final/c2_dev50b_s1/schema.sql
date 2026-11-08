CREATE TABLE "train_information" (
  "train_id" INTEGER,
  "destination" TEXT,
  "price" NUMERIC(10, 2),
  "trainid" INTEGER,
  "arrive by" TIME,
  "duration" INTERVAL,
  "day" TEXT,
  "confirmed reference" INTEGER,
  PRIMARY KEY ("train_id")
);

CREATE TABLE "hotel_information" (
  "hotel_id" INTEGER,
  "type" TEXT,
  "price range" TEXT,
  "confirmed reference" INTEGER,
  "phone" TEXT,
  "stars" INTEGER,
  "address" TEXT,
  "requested stay" INTEGER,
  "area" TEXT,
  "name" TEXT,
  "requested day" TEXT,
  "requested people" INTEGER,
  PRIMARY KEY ("hotel_id")
);

CREATE TABLE "restaurant_information" (
  "restaurant_id" INTEGER,
  "requested time" TIME,
  "requested day" TEXT,
  "postcode" TEXT,
  "requested people" INTEGER,
  "phone" TEXT,
  "address" TEXT,
  "confirmed reference" INTEGER,
  "area" TEXT,
  "food" TEXT,
  "name" TEXT,
  "price range" TEXT,
  PRIMARY KEY ("restaurant_id")
);
