CREATE TABLE "train" (
  "Train arrive by" TIME,
  "Train confirmed reference" INTEGER,
  "Train day" TEXT,
  "Train leave at" TIME,
  "Train price" NUMERIC(10, 2),
  "Train requested people" INTEGER,
  "Train trainid" INTEGER,
  "rest" TEXT,
  PRIMARY KEY ("Train trainid")
);

CREATE TABLE "train_booking" (
  "train_booking id" INTEGER,
  "Train departure" TEXT,
  "Train destination" TEXT,
  PRIMARY KEY ("train_booking id")
);

CREATE TABLE "hotel_booking" (
  "Hotel address" TEXT,
  "Hotel area" TEXT,
  "Hotel confirmed reference" INTEGER,
  "Hotel name" TEXT,
  "Hotel phone" INTEGER,
  "Hotel price range" TEXT,
  "Hotel requested day" TEXT,
  "Hotel requested people" INTEGER,
  "Hotel requested stay" INTEGER,
  "Hotel stars" INTEGER,
  "Hotel type" TEXT,
  "Restaurant address" TEXT,
  "Restaurant area" TEXT,
  "Restaurant confirmed reference" INTEGER,
  "Restaurant food" TEXT,
  "Restaurant name" TEXT,
  "Restaurant phone" INTEGER,
  "Restaurant price range" TEXT,
  "Restaurant requested day" TEXT,
  "Restaurant requested people" INTEGER,
  "Restaurant requested time" TIME,
  "rest" TEXT,
  PRIMARY KEY ("Hotel confirmed reference")
);
