CREATE TABLE "train" (
  "trainid" INTEGER,
  "Train leave at" TIME,
  "Train requested people" INTEGER,
  "Train trainid" INTEGER,
  "Train price" NUMERIC(10, 2),
  "Train duration" INTERVAL,
  "Train departure" TEXT,
  "Train arrive by" TIME,
  "Train destination" TEXT,
  "Train confirmed reference" INTEGER,
  "Train day" TEXT,
  PRIMARY KEY ("trainid")
);

CREATE TABLE "hotel" (
  "hotel id" INTEGER,
  "Hotel requested people" INTEGER,
  "Hotel type" TEXT,
  "Hotel stars" INTEGER,
  "Hotel name" TEXT,
  "Hotel requested day" TEXT,
  "Hotel price range" TEXT,
  "Hotel requested stay" INTEGER,
  PRIMARY KEY ("hotel id")
);

CREATE TABLE "restaurant" (
  "Restaurant phone" INTEGER,
  "Restaurant requested people" INTEGER,
  PRIMARY KEY ("Restaurant phone")
);

CREATE TABLE "event_type" (
  "Hotel postcode" INTEGER,
  "Hotel address" TEXT,
  "Hotel area" TEXT,
  "Hotel confirmed reference" INTEGER,
  "Restaurant food" TEXT,
  "Restaurant postcode" INTEGER,
  "Restaurant area" TEXT,
  "Restaurant requested time" TIME,
  "Restaurant confirmed reference" INTEGER,
  "Restaurant price range" TEXT,
  "Restaurant requested day" TEXT,
  "Restaurant address" TEXT,
  "Restaurant name" TEXT,
  PRIMARY KEY ("Restaurant confirmed reference")
);
