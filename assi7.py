import pymssql
import uuid # for review_id
import datetime # for review date
from decimal import Decimal # for update

# _34hHM4F_QuDUXYOAtqAaw reviewed F0XiRcSbcLF4GwA2A2TDKQ
# tq9Zl18Ml5gwyMRj7ojpGw friend of ^^

conn = pymssql.connect(host='cypress.csil.sfu.ca', user='s_afa85', password='censored', database='afa85354')

# cursor, make connection
cursor = conn.cursor(as_dict=True)

# just to remove errors...
cursor.execute(""" drop trigger if exists update_business_review_count;""")
cursor.execute("""drop trigger if exists check_friend_review;""")

newReviewTrigger = """
                        CREATE TRIGGER update_business_review_count \
                        ON review \
                        AFTER INSERT \
                        AS \
                        BEGIN \
                                IF NOT EXISTS ( \
                                        SELECT 1 \
                                        FROM review r \
                                        JOIN inserted i ON r.user_id = i.user_id AND r.business_id = i.business_id \
                                        WHERE r.review_id <> i.review_id)  \
                                BEGIN \
                                        UPDATE business \
                                        SET review_count = review_count + 1 \
                                        FROM business b \
                                        JOIN inserted i ON b.business_id = i.business_id; \
                                END \
                        END;
                """
cursor.execute(newReviewTrigger)


#star rating is determined by dividing the total stars from all user latest reviews by the total number of reviews submitted by different users
# dont forget to create a README section

# newStarsTrigger = """
#                         CREATE TRIGGER update_business_stars \
#                         ON review \
#                         AFTER INSERT \
#                         AS \
#                         BEGIN \
#                                 IF NOT EXISTS ( \
#                                         SELECT 1 \
#                                         FROM review r \
#                                         JOIN inserted i ON r.user_id = i.user_id AND r.business_id = i.business_id \
#                                         WHERE r.review_id <> i.review_id)  \
#                                 BEGIN \
#                                         UPDATE business \
#                                         SET stars = (review_count*stars + i.stars)/(review_count + 1), review_count = review_count + 1  \
#                                         FROM business b \
#                                         JOIN inserted i ON b.business_id = i.business_id; \
#                                 END \
#                                 ELSE \
#                                 BEGIN \
#                                         UPDATE business \
#                                         SET stars = (review_count*stars - r.stars + i.stars)/review_count \
#                                         FROM business b JOIN inserted i ON b.business_id = i.business_id, review r JOIN inserted i ON r.user_id = i.user_id AND r.business_id = i.business_id; \
#                                 END \
#                         END
#                 """
# cursor.execute(newStarsTrigger)
# combines review and stars update
# if review alr exists, count doesnt go up but stars is replaced
# if review not exist, update stars and count
# need to consider as well the most recent old review to be the one deleted...

friendreviewTrigger = """
                        CREATE TRIGGER check_friend_review \
                        ON review \
                        INSTEAD OF INSERT \
                        AS \
                        BEGIN \
                                IF EXISTS ( \
                                        SELECT 1 \
                                        FROM inserted i \
                                        WHERE NOT EXISTS ( \
                                                SELECT 1 \
                                                FROM friendship f \
                                                JOIN review r ON f.friend = r.user_id \
                                                WHERE f.user_id = i.user_id \
                                                AND r.business_id = i.business_id \
                                                ) \
                                        ) \
                                BEGIN  \
                                        RAISERROR ('User must have at least one friend who has reviewed this business', 16, 1); \
                                END \
                                ELSE \
                                BEGIN \
                                        INSERT INTO review (review_id, user_id, business_id, stars, useful, funny, cool, date) \
                                        SELECT review_id, user_id, business_id, stars, useful, funny, cool, date \
                                        FROM inserted; \
                                END \
                        END
                """
cursor.execute(friendreviewTrigger)


def Login():
        checker = 0
        while checker == 0 :
                username = input("Please enter your user_id: ")
                try:
                        LOGINQUERY = """
                                        SELECT * \
                                        FROM dbo.User_yelp U \
                                        WHERE U.user_id = %s
                                        """
                        cursor.execute(LOGINQUERY, username)
                        row = cursor.fetchone()
                        if row is not None:
                                checker = 1
                                print('Successfully logged in!')
                except:
                        print('invalid user_id. please try again')

        global user_id
        user_id = username

        mainfunction()

                

def searchBusiness():
    # optional: minimum number of stars, city, and name (or part of the name). The search is not case-sensitive. 
    # The user can choose one of the following three orderings of the results: by name, by city, or by number of stars.
        request = "Enter '1' if you'd like only a list of all businesses.\nEnter '2' if you'd like to enter filters.\n"
        input1 = int(input(request))
        if input1 == 1:
                request2 = "choose the column to be ordered in ascension by:  name, city, stars: "
                order = input(request2).lower()
                cursor.execute("""
                                SELECT business_id, name, address, city, stars  \
                                FROM dbo.Business \
                                ORDER BY %s ASC
                                """, order)
                businessRecords = cursor.fetchall()
                for r in businessRecords:
                        print(r)
                        
        elif input1 == 2:
                request2 = "Please enter in the following order: the minimum number of stars(decimal), city, and name(or part of the name).\nLeave empty with a comma if undesired. Eg: 1.2,,Jack\n"
                request3 = "choose the column to be ordered in ascension by:  name, city, stars: "
                istar, icity, iname = input(request2).split(',')
                        #iname is case insensitive in sql in general
                order = input(request3).lower()
                try:
                        if (istar == '') and (icity != '') and (iname != ''):  #if no istar
                                cursor.execute("""
                                                SELECT business_id, name, address, city, stars \
                                                FROM dbo.Business \
                                                WHERE city = %s AND name LIKE %s \
                                                ORDER BY %s ASC""", (icity, '%' + iname + '%', order))
                                businessRecords = cursor.fetchall()
                                if not businessRecords:
                                        print("Sorry, no business fits your criteria.")
                                else:
                                        for r in businessRecords:
                                                print(r)
                                
                        elif (istar != '') and (icity == '') and (iname != ''):  #if no icity
                                istar = float(istar)
                                cursor.execute("""
                                                SELECT business_id, name, address, city, stars \
                                                FROM dbo.Business \
                                                WHERE stars >= %s AND name LIKE %s \
                                                ORDER BY %s ASC""", (istar, '%' + iname + '%', order))
                                businessRecords = cursor.fetchall()
                                if not businessRecords:
                                        print("Sorry, no business fits your criteria.")
                                else:
                                        for r in businessRecords:
                                                print(r)
                        
                        elif (istar != '') and (icity != '') and (iname == ''):  #if no iname
                                istar = float(istar)
                                cursor.execute("""
                                                SELECT business_id, name, address, city, stars \
                                                FROM dbo.Business \
                                                WHERE city = %s AND name LIKE %s \
                                                ORDER BY %s ASC""", (icity, '%' + iname + '%', order))
                                businessRecords = cursor.fetchall()
                                if not businessRecords:
                                        print("Sorry, no business fits your criteria.")
                                else:
                                        for r in businessRecords:
                                                print(r)
                        
                        elif (istar == '') and (icity == '') and (iname != ''):  #if no istar AND icity
                                cursor.execute("""
                                                SELECT business_id, name, address, city, stars \
                                                FROM dbo.Business \
                                                WHERE name LIKE %s \
                                                ORDER BY %s ASC""", ('%' + iname + '%', order))
                                businessRecords = cursor.fetchall()
                                if not businessRecords:
                                        print("Sorry, no business fits your criteria.")
                                else:
                                        for r in businessRecords:
                                                print(r)
                                
                        elif (istar == '') and (icity != '') and (iname == ''):  #if no istar AND iname
                                cursor.execute("""
                                                SELECT business_id, name, address, city, stars \
                                                FROM dbo.Business \
                                                WHERE city = %s \
                                                ORDER BY %s ASC""", (icity, order))
                                businessRecords = cursor.fetchall()
                                if not businessRecords:
                                        print("Sorry, no business fits your criteria.")
                                else:
                                        for r in businessRecords:
                                                print(r)
                        
                        elif (istar != '') and (icity == '') and (iname == ''):  #if no icity AND iname
                                istar = float(istar)
                                cursor.execute("""
                                                SELECT business_id, name, address, city, stars \
                                                FROM dbo.Business \
                                                WHERE istar = %s \
                                                ORDER BY %s ASC""", (istar, order))
                                businessRecords = cursor.fetchall()
                                if not businessRecords:
                                        print("Sorry, no business fits your criteria.")
                                else:
                                        for r in businessRecords:
                                                print(r)
                                
                        elif (istar != '') and (icity != '') and (iname != ''):  #if ALL filters
                                istar = float(istar)
                                cursor.execute("""
                                                SELECT business_id, name, address, city, stars \
                                                FROM dbo.Business \
                                                WHERE city = %s AND istar >= %s AND name LIKE %s \
                                                ORDER BY %s ASC""", (icity, istar, '%' + iname + '%', order))
                                businessRecords = cursor.fetchall()
                                if not businessRecords:
                                        print("Sorry, no business fits your criteria.")
                                else:
                                        for r in businessRecords:
                                                print(r)
                        else:
                                print('if no filters were entered why did you asked for filters in the first place.')
                        
                except Exception as e:
                        print("Oops. Seems like something went wrong.", e)
        
        else:
                print('invalid input.')
                
        request4 = "would you like to review a business? (y/n) "
        input2 = input(request4).lower()
        if input2 == 'y':
                reviewBusiness()
        else:
                print('closing Business query...')

        # for r in businessRecords:
        #         print(r)
        # print(f"{r['business_id']}\t{r['name']}\t{r['address']}\t{r['city']}\t{r['stars']}")
        # must include the following information for each business: id, name, address, city and number of stars

def reviewBusiness():
        # reviewquery = """
        #                 SELECT *  \
        #                 FROM dbo.Review \
        #                 WHERE stars = 5
        #                 """
        # cursor.execute(reviewquery)
        # reviewrecords = cursor.fetchall()
        # for r in reviewrecords:
        #         print(r)
        reviewid = str(uuid.uuid4())
        reviewid = reviewid[:22]
      
        request1 = "Please enter the business_id of the reviewed business: "
        ibusiness = input(request1)
        # no input validation done here

        results = """
                        SELECT review_count, stars \
                        FROM dbo.business \
                        WHERE business_id = %s
                        """
        cursor.execute(results, ibusiness)
        reviewrecord = cursor.fetchone()
        print("business review count:", reviewrecord)

        request2 = "Please enter the integer amount of stars for the reviewed business (1 <= x <= 5)\n "
        istars= (input(request2))

#not asked of me to do useful, funny, and cool
        # request3 = "Please enter the integer amount of useful, funny, and cool for the reviewed business (0 <= x <= 10) Eg. 2,2,0\n "
        # iuseful, ifunny, icool = (input(request3)).split(',')
        iuseful = 0
        ifunny = 0
        icool = 0

        thisdate = datetime.datetime.now()

        try:
                cursor.execute("""SELECT stars \
                               FROM dbo.review \
                               WHERE business_id = %s AND user_id = %s \
                               ORDER BY date DESC""", (ibusiness, user_id))
                oldrevstars = cursor.fetchone()
                istars = Decimal(istars)

                cursor.execute("""SELECT review_count \
                                FROM dbo.business \
                                WHERE business_id = %s""", ibusiness)
                busirev = cursor.fetchone()
                busirev = int(busirev['review_count'])

                cursor.execute("""SELECT stars \
                                FROM dbo.business \
                                WHERE business_id = %s""", ibusiness)
                starsrev = cursor.fetchone()
                starsrev = Decimal(starsrev['stars'])

                ## code not updating the stars
                if oldrevstars is not None:
                        # business in question have been reviewed before, replaces second most recent
                        oldrevstars_value = Decimal(oldrevstars['stars']) # dictionary value extraction

#(review_count * stars - %s + %s)/review_count
                        toSET = (busirev*starsrev - oldrevstars_value + istars)/busirev
                        toSET = Decimal(toSET)
                        print('busirev: ', busirev, ' starsrev: ', starsrev, 'oldrevstars val', oldrevstars_value, 'istars ', istars, 'toset', toSET)
                        cursor.execute("""      
                                        UPDATE dbo.business \
                                        SET stars = %s \
                                        WHERE business_id = %s""", (toSET, ibusiness))
                        conn.commit()
                        
                        cursor.execute(""" SELECT stars FROM dbo.business WHERE business_id = %s""", ibusiness)
                        view = cursor.fetchone()
                        print(view)
                        print('replaced with new stars')
                else:
                        # no review before, adds new stars and averages back!
                        toSET = (busirev*starsrev  + istars)/(busirev + 1)
                        toSET = Decimal(toSET)
                        cursor.execute("""
                                        UPDATE dbo.business \
                                        SET stars = (review_count * stars + %s)/(review_count + 1) \
                                        WHERE business_id = %s""", (toSET, ibusiness))
                        conn.commit()
                        print('got a new star')

                reviewquery = """
                                INSERT INTO dbo.Review \
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """

                # (review_id, user_id, business_id, stars, useful, funny, cool, date) 
                cursor.execute(reviewquery, (reviewid, user_id, ibusiness, istars, iuseful, ifunny, icool, thisdate))
                conn.commit()

                print('Successfully submitted review!') #datetime format is year, month, day, hour, minute, second, microsecond.... argh
                results = """
                                SELECT review_count, stars \
                                FROM dbo.business \
                                WHERE business_id = %s
                                """
                cursor.execute(results, ibusiness)
                reviewrecord = cursor.fetchone()
                print(ibusiness, " business review count:", reviewrecord)
        except:
                print("User must have at least one friend who has reviewed this business.")
# if review alr exists, count doesnt go up but stars is replaced
# if review not exist, update stars and count

# cursor.execute("SELECT * FROM dbo.review WHERE user_id = '_34hHM4F_QuDUXYOAtqAaw'")
# row = cursor.fetchall()
# for r in row:
#         print(r)

# _34hHM4F_QuDUXYOAtqAaw reviewed F0XiRcSbcLF4GwA2A2TDKQ
# tq9Zl18Ml5gwyMRj7ojpGw friend of ^^

# The program should update the number of stars and the count of reviews for the reviewed business.


def searchUser():
        request1 = "Enter '1' if you'd like only a list of all users.\nEnter '2' if you'd like to enter filters.\n"
        input1 = int(input(request1))
        if input1 == 1:
                USERQUERY = """
                                SELECT user_id, name, review_count, useful, funny, cool, average_stars, yelping_since  \
                                FROM dbo.user_yelp \
                                ORDER BY name ASC
                                """
                cursor.execute(USERQUERY)
                userRecords = cursor.fetchall()
                for r in userRecords:
                        print(r)
        elif input1 == 2:
                # I'm not going into the small test cases...
                request2 = "Please enter in the following order: name(or part of the name), minimum number of review count, and minimum average stars.\n Do Not Leave an entry empty. Eg: Tam,1,5.0\n"
                try:
                        iname, irev, iavgstar = input(request2).split(',')
                        #iname is case insensitive in sql in general
                        USERQUERY = """
                                        SELECT user_id, name, review_count, useful, funny, cool, average_stars, yelping_since  \
                                        FROM dbo.user_yelp \
                                        WHERE name LIKE %s AND review_count >= %s AND average_stars >= %s \
                                        ORDER BY name ASC
                                        """
                        irev = int(irev)
                        iavgstar = float(iavgstar)
                        cursor.execute(USERQUERY, ('%' + iname + '%', irev, iavgstar))
                        userRecords = cursor.fetchall()
                        if not userRecords:
                                print('Uh oh... seems like no one fits to your search')
                        else:
                                for r in userRecords:
                                        print(r)
                except:
                        print('oops! something went wrong in your search.')
        else:
                print('invalid input.')

        request3 = "would you like to create friendship? (y/n) "
        input2 = input(request3).lower()
        if input2 == 'y':
                friendship()
        else:
                print('closing user query...')


def friendship():
        request1 = "Please enter the user_id of the person to befriend: "

        checker = 0
        while checker == 0:
                ifriend = input(request1)
                if ifriend == user_id:
                        print("what are you doing.")
                else:
                        checker = 1
        try:
                friendquery = """
                                SELECT * \
                                FROM dbo.friendship \
                                WHERE user_id = %s AND friend = %s
                        """
                # (user_id, friend) assuming the friend's id entered is LEGIT
                cursor.execute(friendquery, (user_id, ifriend))
                print('reached here')
                friendrecords = cursor.fetchall()
                if not friendrecords:
                        friendquery = """
                                        INSERT INTO dbo.friendship \
                                        VALUES (%s, %s)
                                        """

                        cursor.execute(friendquery, (user_id, ifriend))
                        conn.commit()
                        print('Successfully befriended friend!')
                else:
                        print("you have already befriended that friend silly!")

                results = """
                                SELECT friend \
                                FROM dbo.friendship \
                                WHERE user_id = %s
                                """
                cursor.execute(results, user_id)
                friendshipview = cursor.fetchall()

                print("user ", user_id, ", here are your friends:")
                for r in friendshipview:
                        print(r)
        except:
                print("Uh oh! Something went wrong here...")


def mainfunction():
        menu = "1. Search for a Business.\n2. Search for a User.\n3. exit.\nWhat would you like to do? (Please enter a number) "
        usermain = int(input(menu))

        checker = 0
        while (checker == 0):
                if usermain == 1:
                        searchBusiness() # has search AND review
                elif usermain == 2:
                        searchUser() 
                elif usermain == 3:
                        checker = 1
                        break
                usermain = int(input(menu))
        print('thank you for testing this SQL assignment')

# -------------------------------------------------------- where it all begins
Login()

conn.close()
# _34hHM4F_QuDUXYOAtqAaw
