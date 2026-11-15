CREATE TABLE "train" (
  "confirmed reference" INTEGER,
  "Train arrive by" TIME,
  "Train confirmed reference" INTEGER,
  "Train day" TEXT,
  "Train departure" TEXT,
  "Train destination" TEXT,
  "Train duration" INTERVAL,
  "Train leave at" TIME,
  "Train price" NUMERIC(10, 2),
  PRIMARY KEY ("confirmed reference")
);

CREATE TABLE "hotel" (
  "hotel id" INTEGER,
  "Hotel address" TEXT,
  "Hotel confirmed reference" INTEGER,
  "Hotel name" TEXT,
  "Hotel phone" INTEGER,
  "Hotel postcode" INTEGER,
  PRIMARY KEY ("hotel id")
);

CREATE TABLE "restaurant" (
  "Restaurant address" TEXT,
  "Restaurant confirmed reference" INTEGER,
  "Restaurant name" TEXT,
  "Restaurant phone" INTEGER,
  "Restaurant postcode" INTEGER,
  PRIMARY KEY ("Restaurant confirmed reference")
);

CREATE TABLE "train_booking" (
  "trainid" INTEGER,
  "Train requested people" INTEGER,
  "Train trainid" INTEGER,
  PRIMARY KEY ("trainid")
);

CREATE TABLE "hotel_booking" (
  "hotel_booking_id" INTEGER,
  "Hotel area" TEXT,
  "Hotel price range" TEXT,
  "Hotel requested day" TEXT,
  "Hotel requested people" INTEGER,
  "Hotel requested stay" INTEGER,
  "Hotel stars" INTEGER,
  "Hotel type" TEXT,
  "Restaurant area" TEXT,
  "Restaurant food" TEXT,
  "Restaurant price range" TEXT,
  "Restaurant requested day" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant requested time" TIME,
  PRIMARY KEY ("hotel_booking_id")
);
