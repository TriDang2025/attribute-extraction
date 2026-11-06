CREATE TABLE "train_information" (
  "train_booking_id" INTEGER,
  "Train leave at" TIME,
  "Train price" NUMERIC(10, 2),
  "Train requested people" INTEGER,
  "Train trainid" INTEGER,
  "Train duration" INTERVAL,
  "Train departure" TEXT,
  "Train destination" TEXT,
  "Train arrive by" TIME,
  "Train day" TEXT,
  "Train confirmed reference" INTEGER,
  PRIMARY KEY ("train_booking_id")
);

CREATE TABLE "hotel_information" (
  "hotel_booking_id" INTEGER,
  "Hotel confirmed name" TEXT,
  "Hotel name" TEXT,
  "Hotel stars" INTEGER,
  "Hotel type" TEXT,
  "Hotel phone" INTEGER,
  "Hotel postcode" INTEGER,
  "Hotel price range" TEXT,
  "Hotel requested day" TEXT,
  "Hotel requested people" INTEGER,
  "Hotel requested stay" INTEGER,
  "Hotel confirmed reference" INTEGER,
  "Hotel address" TEXT,
  "Hotel area" TEXT,
  "Hotel parking" TEXT,
  PRIMARY KEY ("hotel_booking_id")
);

CREATE TABLE "restaurant_information" (
  "restaurant_booking_id" INTEGER,
  "Restaurant address" TEXT,
  "Restaurant area" TEXT,
  "Restaurant confirmed reference" INTEGER,
  "Restaurant food" TEXT,
  "Restaurant name" TEXT,
  "Restaurant phone" INTEGER,
  "Restaurant postcode" INTEGER,
  "Restaurant price range" TEXT,
  "Restaurant requested day" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant requested time" TIME,
  PRIMARY KEY ("restaurant_booking_id")
);
