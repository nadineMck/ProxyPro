# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 20:25:19 2023

@author: User
"""

import pandas as pd
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tqdm import tqdm

class emailer: 
    def __init__(self):
        self.cc = ["nss32@mail.aub.edu", "sadek.najla@gmail.com","nnm30@mail.aub.edu"] 
        self.df = np.array(pd.read_excel(r"C:\Users\User\Desktop\AUB\4-Fall 23-24\EECE 351\final project\email\testlist.xlsx"))
        self.sender = "proxypro23@outlook.com"

    def  send(self):
        try:
            df =self.df
            sender = self.sender
            cc = self.cc
            for r in tqdm(df): # loop over the rows of the excel file
                print(r)
                email = MIMEMultipart('alternative')
                email["From"] = sender
                email["To"] = r[3]
                email["Cc"] = "; ".join(cc)
                email["Subject"] = "Team 11 - EECE 351 project"

                content = f"""
                <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Recital</title>
            </head>
            <table style="color:black">
                    <tr>
                        <td>
                            <img src="https://raw.githubusercontent.com/najlasadek/images/main/jpegbanner1.jpeg" alt="Image 1" width="100%">
                        </td>
                    </tr>
                    <tr>
                        <td>
                        <p >
                        Hello dear {r[1]} {r[2]},<br><br>

            We are team 11: the only team with 2 members.<br><br>
            If you have received this email, it means that we have successfully <b>made it!</b>. This email especially customized to you (automated email system) is the
            only one of the additional features we implemented.
            <br><br>
            The additional features are:


            <p>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Automated email system<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Web interface <br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Downloading files<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Firewall attack detection<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Multithreading<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Cache expiry date<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Cache storage optimization<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  SQL injection pattern detection<br>
                

            </p>


            We appreciate your attention, the presentation is about to begin!
            <br><br>
            <b> Nadine Mcheik & Najla Sadek </b>


              """   
                # add the components to the email
                html_part = MIMEText(content, 'html') 
                email.attach(html_part)

                smtp = smtplib.SMTP("smtp-mail.outlook.com", port=587)
                smtp.starttls()
                smtp.login(sender, "proxypro2023") #add the password of the sender's account
                # r[3] is the email address of the recipient. we add to it the ccd addresses.
                print(r)
                recipient = [r[3]]
                r3 = recipient+cc
                email = email.as_string()
                smtp.sendmail(sender,r3, email) # the line that sends the email
                smtp.quit()
        
        except Exception as e:
            print(e)
            raise Exception(e)