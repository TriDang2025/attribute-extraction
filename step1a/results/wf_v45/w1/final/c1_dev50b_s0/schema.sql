CREATE TABLE "train" (
  "Train arrive by" TIME,
  "Train confirmed reference" INTEGER,
  "Train day" TEXT,
  "Train departure" TEXT,
  "Train destination" TEXT,
  "Train duration" INTERVAL,
  "Train leave at" TIME,
  "Train price" NUMERIC(10, 2),
  "Train requested people" INTEGER,
  "Train trainid" INTEGER,
  "Hotel postcode" INTEGER,
  "Restaurant postcode" TEXT,
  PRIMARY KEY ("Train trainid")
);

CREATE TABLE "hotel" (
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
  PRIMARY KEY ("Hotel confirmed reference")
);

CREATE TABLE "restaurant" (
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
  PRIMARY KEY ("Restaurant confirmed reference")
);
