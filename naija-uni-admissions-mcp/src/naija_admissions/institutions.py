"""Seed list of Nigerian tertiary institutions.

Auto-generated from regulatory sources (NUC, NBTE, NCCE, NMCN, JAMB IBASS).
Do not edit manually - run discovery.py to refresh.
"""


from .models import InstitutionSeed, InstitutionType, OwnershipType

ALL_INSTITUTIONS: list[InstitutionSeed] = [
    InstitutionSeed(
    name="Abubakar Tafawa Balewa University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Bauchi",
    website="https://www.atbu.edu.ng",
    year_established=1988
    ),
    InstitutionSeed(
    name="Ahmadu Bello University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Zaria",
    website="https://www.abu.edu.ng",
    year_established=1962
    ),
    InstitutionSeed(
    name="Bayero University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Kano",
    website="https://www.buk.edu.ng",
    year_established=1975
    ),
    InstitutionSeed(
    name="Federal University Gashua",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Yobe",
    website="https://www.fugashua.edu.ng",
    year_established=2013
    ),
    InstitutionSeed(
    name="Federal University of Petroleum Resources",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Effurun",
    website="https://www.fupre.edu.ng",
    year_established=2007
    ),
    InstitutionSeed(
    name="Federal University of Technology",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Akure",
    website="https://www.futa.edu.ng",
    year_established=1981
    ),
    InstitutionSeed(
    name="Federal University of Technology",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Minna",
    website="https://www.futminna.edu.ng",
    year_established=1982
    ),
    InstitutionSeed(
    name="Federal University of Technology",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Owerri",
    website="https://www.futo.edu.ng",
    year_established=1980
    ),
    InstitutionSeed(
    name="Federal University Dutse",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Jigawa State",
    website="https://www.fud.edu.ng",
    year_established=2011
    ),
    InstitutionSeed(
    name="Federal University Dutsin-Ma",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Katsina",
    website="https://www.fudutsinma.edu.ng",
    year_established=2011
    ),
    InstitutionSeed(
    name="Federal University Kashere",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Gombe State",
    website="https://www.fukashere.edu.ng",
    year_established=2011
    ),
    InstitutionSeed(
    name="Federal University Lafia",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Nasarawa State",
    website="https://www.fulafia.edu.ng",
    year_established=2011
    ),
    InstitutionSeed(
    name="Federal University Lokoja",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Kogi State",
    website="https://www.fulokoja.edu.ng",
    year_established=2011
    ),
    InstitutionSeed(
    name="Alex Ekwueme University,Ndufu-Alike",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Ebonyi State",
    website="https://www.funai.edu.ng",
    year_established=2011
    ),
    InstitutionSeed(
    name="Federal University Otuoke",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Bayelsa",
    website="https://www.fuotuoke.edu.ng",
    year_established=2011
    ),
    InstitutionSeed(
    name="Federal University Oye-Ekiti",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Ekiti State",
    website="https://www.fuoye.edu.ng",
    year_established=2011
    ),
    InstitutionSeed(
    name="Federal University Wukari",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Taraba State",
    website="https://www.fuwukari.edu.ng",
    year_established=2011
    ),
    InstitutionSeed(
    name="Federal University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Birnin Kebbi",
    website="https://www.fubk.edu.ng",
    year_established=2013
    ),
    InstitutionSeed(
    name="Federal University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    state="Gusau Zamfara",
    website="https://www.fugusau.edu.ng",
    year_established=2013
    ),
    InstitutionSeed(
    name="Michael Okpara University of Agricultural Umudike",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.FEDERAL,
    website="https://www.mouau.edu.ng",
    year_established=1992
    ),
    InstitutionSeed(
    name="Rivers State University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.STATE,
    website="https://www.rsu.edu.ng",
    year_established=1979
    ),
    InstitutionSeed(
    name="Ambrose Alli University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.STATE,
    state="Ekpoma",
    website="https://www.aauekpoma.edu.ng",
    year_established=1980
    ),
    InstitutionSeed(
    name="Abia State University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.STATE,
    state="Uturu",
    website="https://www.abiastateuniversity.edu.ng",
    year_established=1981
    ),
    InstitutionSeed(
    name="Ekiti State University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.STATE,
    website="https://www.eksu.edu.ng",
    year_established=1982
    ),
    InstitutionSeed(
    name="Enugu State University of Science and Technology",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.STATE,
    state="Enugu",
    website="https://www.esut.edu.ng",
    year_established=1982
    ),
    InstitutionSeed(
    name="Olabisi Onabanjo University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.STATE,
    state="Ago Iwoye",
    website="https://www.oouagoiwoye.edu.ng",
    year_established=1982
    ),
    InstitutionSeed(
    name="Lagos State University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.STATE,
    state="Ojo",
    website="https://www.lasu.edu.ng",
    year_established=1983
    ),
    InstitutionSeed(
    name="Ladoke Akintola University of Technology",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.STATE,
    state="Ogbomoso",
    website="https://www.lautech.edu.ng",
    year_established=1990
    ),
    InstitutionSeed(
    name="Rev. Fr. Moses Orshio Adasu (Formerly,Benue State University)",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.STATE,
    state="Makurdi",
    website="https://www.bsum.edu.ng",
    year_established=1992
    ),
    InstitutionSeed(
    name="Delta State University Abraka",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.STATE,
    website="https://www.delsu.edu.ng",
    year_established=1992
    ),
    InstitutionSeed(
    name="Babcock University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Ilishan-Remo",
    website="https://www.babcock.edu.ng",
    year_established=1999
    ),
    InstitutionSeed(
    name="Igbinedion University Okada",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    website="https://www.iuokada.edu.ng",
    year_established=1999
    ),
    InstitutionSeed(
    name="Madonna University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Okija",
    website="https://www.madonnauniversity.edu.ng",
    year_established=1999
    ),
    InstitutionSeed(
    name="Bowen University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Iwo",
    website="https://www.bowen.edu.ng",
    year_established=2001
    ),
    InstitutionSeed(
    name="Benson Idahosa University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Benin City",
    website="https://www.biu.edu.ng",
    year_established=2002
    ),
    InstitutionSeed(
    name="Covenant University Ota",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    website="https://www.covenantuniversity.edu.ng",
    year_established=2002
    ),
    InstitutionSeed(
    name="Pan-Atlantic University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Lagos",
    website="https://www.pau.edu.ng",
    year_established=2002
    ),
    InstitutionSeed(
    name="American University of Nigeria",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Yola",
    website="https://www.aun.edu.ng",
    year_established=2003
    ),
    InstitutionSeed(
    name="Ajayi Crowther University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Ibadan",
    website="https://www.acu.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="Al-Hikmah University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Ilorin",
    website="https://www.alhikmah.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="Al-Qalam University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Katsina",
    website="https://www.auk.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="Bells University of Technology",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Otta",
    website="https://www.bellsuniversity.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="Bingham University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="New Karu",
    website="https://www.binghamuni.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="Caritas University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Enugu",
    website="https://www.caritasuni.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="Crawford University Igbesa",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    website="https://www.crawforduniversity.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="Crescent University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    website="https://www.crescent-university.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="Kwararafa University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Wukari",
    website="https://www.kwararafauniversity.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="Lead City University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Ibadan",
    website="https://www.lcu.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="Novena University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Ogume",
    website="https://www.novenauniversity.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="Redeemer's University",
    institution_type=InstitutionType.UNIVERSITY,
    type=OwnershipType.PRIVATE,
    state="Ede",
    website="https://www.run.edu.ng",
    year_established=2005
    ),
    InstitutionSeed(
    name="A.D. Rufa’i College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="Abdullahi Maikano College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Plateau"
    ),
    InstitutionSeed(
    name="Abubakar Garba Zagada- Zagada College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Gombe"
    ),
    InstitutionSeed(
    name="Abubakar Tatari Polytechnic",
    institution_type=InstitutionType.POLYTECHNIC,
    type=OwnershipType.STATE,
    state="Bauchi",
    website="https://[rector@atapolybauci.com](https://rector@atapolybauci.com)"
    ),
    InstitutionSeed(
    name="Adamu Augie College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kebbi"
    ),
    InstitutionSeed(
    name="Adamu Garkuwa COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="Adamu Tafawa Balewa COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Bauchi",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="Adesina College of Education, Share",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara",
    website="https://[www.adesinacollege.edu.ng](https://www.adesinacollege.edu.ng)"
    ),
    InstitutionSeed(
    name="Adigrace COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Taraba"
    ),
    InstitutionSeed(
    name="African Thinkers Community of Inquiry COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Enugu",
    website="https://[www.atcoicoe.edu.ng](https://www.atcoicoe.edu.ng)"
    ),
    InstitutionSeed(
    name="Ahlus-Suffah COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kaduna"
    ),
    InstitutionSeed(
    name="Ajetumobi COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="Akwa Ibom State College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Akwa Ibom"
    ),
    InstitutionSeed(
    name="AL HIKMA COLLEGE OF EDUCATION",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kogi"
    ),
    InstitutionSeed(
    name="Al-fajr College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano"
    ),
    InstitutionSeed(
    name="Al-Ibadan COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ibadan"
    ),
    InstitutionSeed(
    name="Al-Iman College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Plateau"
    ),
    InstitutionSeed(
    name="Al-Madinah COE Oshogbo",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Osun"
    ),
    InstitutionSeed(
    name="Al-Mustafa College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano",
    website="https://[mcekano.edu.ng](https://mcekano.edu.ng)"
    ),
    InstitutionSeed(
    name="Al-Ummah COE (UMCOED)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Osun"
    ),
    InstitutionSeed(
    name="Ameenuddeen College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano",
    website="https://[SomethingEdu.ng](https://SomethingEdu.ng)"
    ),
    InstitutionSeed(
    name="Ameer Shehu Idris College of Advanced Studies",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kaduna"
    ),
    InstitutionSeed(
    name="Aminu Kano College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano"
    ),
    InstitutionSeed(
    name="Aminu Kano College of Islamic and Legal Studies",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kano"
    ),
    InstitutionSeed(
    name="Aminu Sale College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="Angel Crown COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="FCT Abuja"
    ),
    InstitutionSeed(
    name="Annur College of Education Kano",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano"
    ),
    InstitutionSeed(
    name="Ansar-Ud-Deen College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Lagos"
    ),
    InstitutionSeed(
    name="Apa COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue"
    ),
    InstitutionSeed(
    name="Archbishop Alexander Ibezim COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Anambra",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="Assanusiya COE, Odeomu",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Osun"
    ),
    InstitutionSeed(
    name="Awori District COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ogun"
    ),
    InstitutionSeed(
    name="Bauchi Institute for Arabic and Islamic Studies",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="Bayo Tijani COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Lagos"
    ),
    InstitutionSeed(
    name="Benjamin Uwajumogu (State) College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Imo",
    website="https://[imsced.edu.ng](https://imsced.edu.ng)"
    ),
    InstitutionSeed(
    name="Best Legacy COE Ogbomoso",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Oyo"
    ),
    InstitutionSeed(
    name="BETHEL COE IJARE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ondo"
    ),
    InstitutionSeed(
    name="Biga College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Sokoto"
    ),
    InstitutionSeed(
    name="Bogoro College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="Bright College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kaduna",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Calvin Foundation COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue"
    ),
    InstitutionSeed(
    name="Christian Chukwuma Onoh COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Enugu"
    ),
    InstitutionSeed(
    name="Christian College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Gombe"
    ),
    InstitutionSeed(
    name="City College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="FCT Abuja"
    ),
    InstitutionSeed(
    name="Climax College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Bauchi",
    website="https://[NULL](https://NULL)"
    ),
    InstitutionSeed(
    name="COASTLINE COLLEGE OF EDUCATION",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ondo",
    website="https://[coastlinecollege.edu.ng](https://coastlinecollege.edu.ng)"
    ),
    InstitutionSeed(
    name="COE, Moro",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Osun"
    ),
    InstitutionSeed(
    name="COKWILLS COLLEGE OF EDUCATION",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Lagos",
    website="https://[www.taecoed.edu.ng](https://www.taecoed.edu.ng)"
    ),
    InstitutionSeed(
    name="College of Education (Technical)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Bauchi",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="College of Education Akwanga",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Nasarawa",
    website="https://[coeakwanga.edu.ng](https://coeakwanga.edu.ng)"
    ),
    InstitutionSeed(
    name="College of Education and Entrepreneurship Studies",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="College of Education and Legal Studies",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Yobe",
    website="https://[coelsnguru.edu.ng](https://coelsnguru.edu.ng)"
    ),
    InstitutionSeed(
    name="College of Education Ilemona",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="College of Education Kura",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano"
    ),
    InstitutionSeed(
    name="College of Education llorin",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kwara",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="College of Education Oju",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Benue"
    ),
    InstitutionSeed(
    name="College of Education Oro",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="College of Education, Arochukwu",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Abia"
    ),
    InstitutionSeed(
    name="College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Gombe"
    ),
    InstitutionSeed(
    name="College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Bauchi",
    website="https://[SomethingEdu.ng](https://SomethingEdu.ng)"
    ),
    InstitutionSeed(
    name="College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Plateau",
    website="https://[coeg.edu.ng](https://coeg.edu.ng)"
    ),
    InstitutionSeed(
    name="College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Yola"
    ),
    InstitutionSeed(
    name="College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Ekiti",
    website="https://[www.coeikere.edu.ng](https://www.coeikere.edu.ng)"
    ),
    InstitutionSeed(
    name="College of Education, Ila-Orangun",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Osun",
    website="https://[oscoedilesa.edu.ng](https://oscoedilesa.edu.ng)"
    ),
    InstitutionSeed(
    name="College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Benue"
    ),
    InstitutionSeed(
    name="College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Borno"
    ),
    InstitutionSeed(
    name="College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Delta",
    website="https://[www.coewarri.edu.ng](https://www.coewarri.edu.ng)"
    ),
    InstitutionSeed(
    name="College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Taraba"
    ),
    InstitutionSeed(
    name="Community COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano",
    website="https://[fcekano.edu.ng](https://fcekano.edu.ng)"
    ),
    InstitutionSeed(
    name="Corner Stone College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Lagos"
    ),
    InstitutionSeed(
    name="Corona COE Lekki",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Lagos"
    ),
    InstitutionSeed(
    name="Covenant College of Education (CCOE)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Abia"
    ),
    InstitutionSeed(
    name="Crescent Pearls Technical College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="FCT Abuja",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="CRESTFIELD COLLEGE OF EDUCATION",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Osun"
    ),
    InstitutionSeed(
    name="Cross River State Coll. of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Cross River"
    ),
    InstitutionSeed(
    name="Dala College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano"
    ),
    InstitutionSeed(
    name="Danyaya College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="Dee-Perfect Class College of Education, Ifon-Osun",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Osun"
    ),
    InstitutionSeed(
    name="Delar College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Oyo"
    ),
    InstitutionSeed(
    name="Delta State College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Delta",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="DIAMOND COLLEGE OF EDUCATION",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Abia",
    website="https://[www.dce.edu.ng](https://www.dce.edu.ng)"
    ),
    InstitutionSeed(
    name="Doviana COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue"
    ),
    InstitutionSeed(
    name="Eagle Mountain College of Education Abo Mbaise",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Imo",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Ebenezer College of Education Amangwu",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ebonyi"
    ),
    InstitutionSeed(
    name="Ebonyi State College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Ebonyi"
    ),
    InstitutionSeed(
    name="ECWA COE Igbaja",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="ECWA COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="ECWA College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Plateau",
    website="https://[www.jets.edu.ng](https://www.jets.edu.ng)"
    ),
    InstitutionSeed(
    name="Edexcel College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue",
    website="https://[SomethingEdu.ng](https://SomethingEdu.ng)"
    ),
    InstitutionSeed(
    name="Edo State College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Edo"
    ),
    InstitutionSeed(
    name="Elder Oyama Memorial COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Cross River"
    ),
    InstitutionSeed(
    name="Elibest College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ondo"
    ),
    InstitutionSeed(
    name="Elizabeth Memorial College of Education Nsukka",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Enugu"
    ),
    InstitutionSeed(
    name="Emamor College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Rivers"
    ),
    InstitutionSeed(
    name="Emirate College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Bauchi",
    website="https://[SomethingEdu.ng](https://SomethingEdu.ng)"
    ),
    InstitutionSeed(
    name="Emmanuel Ebije Ikwue College Of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue",
    website="https://[SomethingEdu.ng](https://SomethingEdu.ng)"
    ),
    InstitutionSeed(
    name="Enugu State Coll. of Education (T)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Enugu"
    ),
    InstitutionSeed(
    name="FCT College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="FCT Abuja",
    website="https://[fctcoezuba.com.ng](https://fctcoezuba.com.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education (FCE) Gwoza",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Borno",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education (Special)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Oyo",
    website="https://[www.fceoyo.edu.ng](https://www.fceoyo.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education (T)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Ebonyi"
    ),
    InstitutionSeed(
    name="Federal College of Education (T)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Anambra",
    website="https://[www.fcetumunze.edu.ng](https://www.fcetumunze.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education (Tech)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Yobe",
    website="https://[fcetpotiskum.edu.ng](https://fcetpotiskum.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education (Technical) in Yauri",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Kebbi",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education (Technical)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Lagos"
    ),
    InstitutionSeed(
    name="Federal College of Education (Technical)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Delta"
    ),
    InstitutionSeed(
    name="Federal College of Education (Technical)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Kano",
    website="https://[www.fcetbichi.edu.ng](https://www.fcetbichi.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education (Technical)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Gombe"
    ),
    InstitutionSeed(
    name="Federal College of Education (Technical)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Zamfara"
    ),
    InstitutionSeed(
    name="Federal College of Education (Technical)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Rivers",
    website="https://[www.infor@fcetomoku.edu.com](https://www.infor@fcetomoku.edu.com)"
    ),
    InstitutionSeed(
    name="Federal College of Education Bauchi",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="Federal College of Education Edo",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Edo"
    ),
    InstitutionSeed(
    name="Federal College of Education Ilawe-Ekiti",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Ekiti",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education Ofeme-Ohuhu",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Abia",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education Osun",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Osun",
    website="https://[www.fceiwo.edu.ng](https://www.fceiwo.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education Sokoto",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Sokoto"
    ),
    InstitutionSeed(
    name="Federal College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Ogun",
    website="https://[www.fce.abeokuta.edu.ng](https://www.fce.abeokuta.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Enugu"
    ),
    InstitutionSeed(
    name="Federal College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Akwa Ibom",
    website="https://[www.none.com](https://www.none.com)"
    ),
    InstitutionSeed(
    name="Federal College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Katsina"
    ),
    InstitutionSeed(
    name="Federal College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Cross River",
    website="https://[www.fceobudu.edu.ng](https://www.fceobudu.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education, Odugbo",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Benue"
    ),
    InstitutionSeed(
    name="Federal College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Kogi",
    website="https://[www.fceokene.edu.ng](https://www.fceokene.edu.ng)"
    ),
    InstitutionSeed(
    name="Federal College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Adamawa",
    website="https://[www.fceyolanigeria.org](https://www.fceyolanigeria.org)"
    ),
    InstitutionSeed(
    name="Federal College Of Education(Technical)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.FEDERAL,
    state="Nasarawa",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="FESTMED COLLEGE OF EDUCATION",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ondo",
    website="https://[www.coea-edu.com](https://www.coea-edu.com)"
    ),
    InstitutionSeed(
    name="First De-Wise College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Folrac Fortified College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ondo",
    website="https://[ffcoe.edu.ng](https://ffcoe.edu.ng)"
    ),
    InstitutionSeed(
    name="Gand-Plus College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="Gboko College of Education Benue State",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue"
    ),
    InstitutionSeed(
    name="Global COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Plateau"
    ),
    InstitutionSeed(
    name="Gombe State COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Gombe"
    ),
    InstitutionSeed(
    name="Good Shepperd COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ogun"
    ),
    InstitutionSeed(
    name="GRACE COLLEGE OF EDUCATION",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Osun"
    ),
    InstitutionSeed(
    name="Hamzainab College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Osun"
    ),
    InstitutionSeed(
    name="Hassan Usman Katsina Polytechnic",
    institution_type=InstitutionType.POLYTECHNIC,
    type=OwnershipType.STATE,
    state="Katsina"
    ),
    InstitutionSeed(
    name="Havard Wilson College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Abia"
    ),
    InstitutionSeed(
    name="Hill COE, Gwanje",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Nasarawa",
    website="https://[Not Available](https://Not%20Available)"
    ),
    InstitutionSeed(
    name="His Grace College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="Hope and Anchor College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Niger"
    ),
    InstitutionSeed(
    name="Ife College of Education Omala",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="kogi"
    ),
    InstitutionSeed(
    name="Ikeduru College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Imo",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="Imam Hamzat COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="Imam Saidu COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Katsina"
    ),
    InstitutionSeed(
    name="Innovative College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Nasarawa"
    ),
    InstitutionSeed(
    name="Institute of Ecumenical Education (Thinkers Corner)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Enugu"
    ),
    InstitutionSeed(
    name="International College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Plateau",
    website="https://[SomethingEdu.ng](https://SomethingEdu.ng)"
    ),
    InstitutionSeed(
    name="Isa Kaita College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Katsina"
    ),
    InstitutionSeed(
    name="Isaac Jasper Boro COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Bayelsa"
    ),
    InstitutionSeed(
    name="Islamic COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Yobe",
    website="https://[Not Available](https://Not%20Available)"
    ),
    InstitutionSeed(
    name="JIBWIS COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="JIBWIS COE, Jega",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kebbi",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="Jibwis COE, Zuru",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kebbi"
    ),
    InstitutionSeed(
    name="JIBWIS College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Nasarawa"
    ),
    InstitutionSeed(
    name="JIBWIS College of Education Gombe",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Gombe"
    ),
    InstitutionSeed(
    name="JIBWIS College of Education Jos",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Plateau"
    ),
    InstitutionSeed(
    name="Jibwis College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="JIGAWA STATE COLLEGE OF EDUCATION AND LEGAL STUDIES",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Jigawa",
    website="https://[www.jscilsringim.edu.ng](https://www.jscilsringim.edu.ng)"
    ),
    InstitutionSeed(
    name="Jigawa State College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Jigawa",
    website="https://[jscoeg.edu.ng](https://jscoeg.edu.ng)"
    ),
    InstitutionSeed(
    name="Jigawa State Polytechnic",
    institution_type=InstitutionType.POLYTECHNIC,
    type=OwnershipType.STATE,
    state="Jigwa"
    ),
    InstitutionSeed(
    name="Job College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Osun",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Jornato College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue"
    ),
    InstitutionSeed(
    name="Kaduna Polytechnics",
    institution_type=InstitutionType.POLYTECHNIC,
    type=OwnershipType.STATE,
    state="Kaduna"
    ),
    InstitutionSeed(
    name="Kaduna State College of Education, Gidan-Waya",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kaduna"
    ),
    InstitutionSeed(
    name="Kano State College of Education and Preliminary Studies (KASCEPTS)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kano",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="Kano State Polytechnic",
    institution_type=InstitutionType.POLYTECHNIC,
    type=OwnershipType.STATE,
    state="Kano"
    ),
    InstitutionSeed(
    name="Kashim Ibrahim College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Borno",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="Kazaure College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Jigawa"
    ),
    InstitutionSeed(
    name="Kebbi State Polytechnic",
    institution_type=InstitutionType.POLYTECHNIC,
    type=OwnershipType.STATE,
    state="Kebbi",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="Kinsey College Of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara",
    website="https://[SomethingEdu.ng](https://SomethingEdu.ng)"
    ),
    InstitutionSeed(
    name="Kogi East College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kogi"
    ),
    InstitutionSeed(
    name="Kogi State College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kogi",
    website="https://[www.kscoeankpa.edu.ng](https://www.kscoeankpa.edu.ng)"
    ),
    InstitutionSeed(
    name="Kogi State College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kogi"
    ),
    InstitutionSeed(
    name="Kwaine COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Gombe",
    website="https://[non.edu.ng](https://non.edu.ng)"
    ),
    InstitutionSeed(
    name="Kwara State College of Education (Technical)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kwara",
    website="https://[https://www.kwacoet.edu.ng](https://https://www.kwacoet.edu.ng)"
    ),
    InstitutionSeed(
    name="Kwararafa COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue"
    ),
    InstitutionSeed(
    name="Lakeview COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Taraba",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Lasting Glory College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Oyo",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Lessel COE Gboko",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue"
    ),
    InstitutionSeed(
    name="Lifegate College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="MARYAM IDRIS UMAR COLLEGE OF EDUCATION LIMITED",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano",
    website="https://[SomethingEdu.ng](https://SomethingEdu.ng)"
    ),
    InstitutionSeed(
    name="MCF COE Agbarha-Otor",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Delta"
    ),
    InstitutionSeed(
    name="Meadow Hall COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Lagos"
    ),
    InstitutionSeed(
    name="Metro COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Nasarawa"
    ),
    InstitutionSeed(
    name="Moje College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="Muftau Olanihun College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Oyo"
    ),
    InstitutionSeed(
    name="Muhammad Goni College of Legal and Islamic Studies (MOGOLIS)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Borno"
    ),
    InstitutionSeed(
    name="Muhyideen College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="Muritadha COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Oyo",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Mus'ab Bn Umair College of Education Bajoga",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Gombe"
    ),
    InstitutionSeed(
    name="Nana Aishat Memorial COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="National Institute for Nigerian Languages",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Abia",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="National Teachers Institute(NTI)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kaduna"
    ),
    InstitutionSeed(
    name="Niger State College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Niger",
    website="https://[www.coeminna.edu.ng](https://www.coeminna.edu.ng)"
    ),
    InstitutionSeed(
    name="Nigerian Army College of Education (NACOE)",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kwara",
    website="https://[nacoe.edu.ng](https://nacoe.edu.ng)"
    ),
    InstitutionSeed(
    name="Nosakhare COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Edo"
    ),
    InstitutionSeed(
    name="Nuhu Bamalli Polytechnic",
    institution_type=InstitutionType.POLYTECHNIC,
    type=OwnershipType.STATE,
    state="Kaduna",
    website="https://[nubapoly.edu.ng](https://nubapoly.edu.ng)"
    ),
    InstitutionSeed(
    name="Nwafor Orizu College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Anambra",
    website="https://[nocen.edu.ng](https://nocen.edu.ng)"
    ),
    InstitutionSeed(
    name="Olekamba College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ondo"
    ),
    InstitutionSeed(
    name="Omaga aejigbo College of education Ajiolo-Ojiaji",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kogi"
    ),
    InstitutionSeed(
    name="ONIT COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Anambra"
    ),
    InstitutionSeed(
    name="Osan Ekiti COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ekiti",
    website="https://[osanekiticoe.com](https://osanekiticoe.com)"
    ),
    InstitutionSeed(
    name="Osi College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Osisa Tech. College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Enugu"
    ),
    InstitutionSeed(
    name="Oswald Waller COE Shendam",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Plateau"
    ),
    InstitutionSeed(
    name="Owu College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ogu"
    ),
    InstitutionSeed(
    name="Oyo State College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Oyo",
    website="https://[oyscoel.edu.ng](https://oyscoel.edu.ng)"
    ),
    InstitutionSeed(
    name="Pan Africa Entrepreneurship and Vocational College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Lagos",
    website="https://[panafricaninstitute.org](https://panafricaninstitute.org)"
    ),
    InstitutionSeed(
    name="PAN African COE Offa",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara"
    ),
    InstitutionSeed(
    name="Peace College Of Education Ankpa",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kogi"
    ),
    InstitutionSeed(
    name="Peaceland College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Enugu",
    website="https://[www.peaceland.edu,ng](https://www.peaceland.edu,ng)"
    ),
    InstitutionSeed(
    name="Peacock College of Education Jalingo",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Taraba"
    ),
    InstitutionSeed(
    name="Peter Oyeleye Fasua College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ondo",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Petriot College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Oyo",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Piaget College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ogun",
    website="https://[Not Available](https://Not%20Available)"
    ),
    InstitutionSeed(
    name="Pineville College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Oyo",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Plateau State Polytechnic",
    institution_type=InstitutionType.POLYTECHNIC,
    type=OwnershipType.STATE,
    state="Plataeu"
    ),
    InstitutionSeed(
    name="Premier COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Osun"
    ),
    InstitutionSeed(
    name="Pristine College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Imo",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Providence International College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Oyo",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Ramat Polytechnic",
    institution_type=InstitutionType.POLYTECHNIC,
    type=OwnershipType.STATE,
    state="Borno"
    ),
    InstitutionSeed(
    name="Raphat COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Osun"
    ),
    InstitutionSeed(
    name="Royal City COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ogun"
    ),
    InstitutionSeed(
    name="Royal COE, Ikeja",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Lagos"
    ),
    InstitutionSeed(
    name="Royal College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ogun"
    ),
    InstitutionSeed(
    name="S. Light College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Sa'adatu Rimi College of Education, Kumbotso",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kano"
    ),
    InstitutionSeed(
    name="Sam Ale College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="FCT Abuja"
    ),
    InstitutionSeed(
    name="Sarkin Yama Community College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Bauchi"
    ),
    InstitutionSeed(
    name="Sharifat Institute of Professional and Islamic Legal Studies",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara",
    website="https://[sharifatcoeils.edu.ng](https://sharifatcoeils.edu.ng)"
    ),
    InstitutionSeed(
    name="Shehu Shagari College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Sokoto"
    ),
    InstitutionSeed(
    name="Sikiru Adetona College of Education, Science and Technology",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Ogun",
    website="https://[www.tasce.edu.ng](https://www.tasce.edu.ng)"
    ),
    InstitutionSeed(
    name="Sinai COE & Ent. Studies Gboko",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue"
    ),
    InstitutionSeed(
    name="St. Augustine College of Education Akoka",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Lagos"
    ),
    InstitutionSeed(
    name="St. Frances Asissi College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kaduna"
    ),
    InstitutionSeed(
    name="St. Paul's College of Education NNewi",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Anambra"
    ),
    InstitutionSeed(
    name="STEADY FLOW COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Cross River"
    ),
    InstitutionSeed(
    name="Talent Finders College of Education, Ilala",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara",
    website="https://[SomethingEdu.ng](https://SomethingEdu.ng)"
    ),
    InstitutionSeed(
    name="Tamic COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Lagos",
    website="https://[NON.EDU.NG](https://NON.EDU.NG)"
    ),
    InstitutionSeed(
    name="TCNN College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Plateau"
    ),
    InstitutionSeed(
    name="The College of Education Iseyin",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Oyo",
    website="https://[coediseyin.edukate.ng](https://coediseyin.edukate.ng)"
    ),
    InstitutionSeed(
    name="The College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Enugu"
    ),
    InstitutionSeed(
    name="The Heritage College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ondo",
    website="https://[SomethingEdu.ng](https://SomethingEdu.ng)"
    ),
    InstitutionSeed(
    name="The Polytechnic Iree",
    institution_type=InstitutionType.POLYTECHNIC,
    type=OwnershipType.STATE,
    state="Osun"
    ),
    InstitutionSeed(
    name="Tijjani Ibrahim College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano"
    ),
    InstitutionSeed(
    name="Tony G Erewa College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Delta",
    website="https://[tonygerewacoe.com.ng](https://tonygerewacoe.com.ng)"
    ),
    InstitutionSeed(
    name="Top Sprout Coe",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kwara",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="Top-Most COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Lagos"
    ),
    InstitutionSeed(
    name="Turath COE",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kano"
    ),
    InstitutionSeed(
    name="Uli College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Anambra"
    ),
    InstitutionSeed(
    name="Umar Bun Khatab College of Education, Tudun Nupawa",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kaduna"
    ),
    InstitutionSeed(
    name="Umar Ibn Ibrahim El-Kanemi College of Education, Science and Technology",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Borno"
    ),
    InstitutionSeed(
    name="Umar Suleiman College of Education Gashua",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Yobe",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="Unity College of Education, Aukpa Adoka",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Benue",
    website="https://[-](https://-)"
    ),
    InstitutionSeed(
    name="Upland College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ondo",
    website="https://[upland.edu.ng](https://upland.edu.ng)"
    ),
    InstitutionSeed(
    name="Victory Belt College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Kogi",
    website="https://[victorybeltintlminitries.com/college-of-education/](https://victorybeltintlminitries.com/college-of-education/)"
    ),
    InstitutionSeed(
    name="WATERSIDE COLLEGE OF EDUCATION",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ogun",
    website="https://[nodomain.edu.ng](https://nodomain.edu.ng)"
    ),
    InstitutionSeed(
    name="Waziri Umaru Federal Polytechnic",
    institution_type=InstitutionType.POLYTECHNIC,
    type=OwnershipType.STATE,
    state="Kebbi"
    ),
    InstitutionSeed(
    name="Yewa Central College of Education, Ayetoro",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.PRIVATE,
    state="Ogun"
    ),
    InstitutionSeed(
    name="Yusuf Bala Usman CoE and Legal Studies",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Katsina",
    website="https://[none.edu.ng](https://none.edu.ng)"
    ),
    InstitutionSeed(
    name="Yusuf Maitama Sule COE and Lege Studeis",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kano",
    website="https://[yumsceas.com.ng](https://yumsceas.com.ng)"
    ),
    InstitutionSeed(
    name="Zamfara State College of Education",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Zamfara"
    ),
    InstitutionSeed(
    name="Zaria Institute of Information Technology",
    institution_type=InstitutionType.COLLEGE_OF_EDUCATION,
    type=OwnershipType.STATE,
    state="Kaduna"
    ),
]


# Helper functions

def filter_by_type(institutions: list[InstitutionSeed], inst_types: list[InstitutionType] | None = None) -> list[InstitutionSeed]:
    if inst_types is None:
        return institutions
    return [s for s in institutions if s.institution_type in inst_types]


def filter_by_ownership(ownership: OwnershipType) -> list[InstitutionSeed]:
    return [s for s in ALL_INSTITUTIONS if s.type == ownership]


def filter_by_state(state: str) -> list[InstitutionSeed]:
    state_lower = state.lower()
    return [s for s in ALL_INSTITUTIONS if s.state and s.state.lower() == state_lower]


def seed_counts() -> dict[str, int]:
    counts = {
        "total": len(ALL_INSTITUTIONS),
        "by_type": {},
        "by_ownership": {},
        "by_state": {},
    }
    for s in ALL_INSTITUTIONS:
        t = s.institution_type.value
        counts["by_type"][t] = counts["by_type"].get(t, 0) + 1
        o = s.type.value
        counts["by_ownership"][o] = counts["by_ownership"].get(o, 0) + 1
        if s.state:
            counts["by_state"][s.state] = counts["by_state"].get(s.state, 0) + 1
    return counts
