CREATE TABLE "train_information" (
  "train_id" INTEGER,
  "departure" TEXT,
  "destination" TEXT,
  "leave at" TIME,
  "price" NUMERIC(10, 2),
  "day" TEXT,
  "requested people" INTEGER,
  "confirmed reference" INTEGER,
  "duration" INTERVAL,
  "Train trainid" INTEGER,
  PRIMARY KEY ("train_id")
);

CREATE TABLE "hotel_information" (
  "hotel_id" INTEGER,
  "area" TEXT,
  "name" TEXT,
  "postcode" INTEGER,
  "confirmed reference" INTEGER,
  "requested people" INTEGER,
  "requested stay" INTEGER,
  "requested day" TEXT,
  "type" TEXT,
  "address" TEXT,
  "price range" TEXT,
  PRIMARY KEY ("hotel_id")
);

CREATE TABLE "restaurant_information" (
  "restaurant_id" INTEGER,
  "confirmed reference" INTEGER,
  "address" TEXT,
  "requested day" TEXT,
  "requested people" INTEGER,
  "area" TEXT,
  "food" TEXT,
  "price range" TEXT,
  "phone" INTEGER,
  "requested time" TIME,
  "name" TEXT,
  PRIMARY KEY ("restaurant_id")
);
