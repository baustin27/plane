/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { AuthBase } from "@/components/auth-screens/auth-base";
import { LogoSpinner } from "@/components/common/logo-spinner";
import { EAuthModes, EPageTypes } from "@/helpers/authentication.helper";
import DefaultLayout from "@/layouts/default-layout";
import { AuthenticationWrapper } from "@/lib/wrappers/authentication-wrapper";
import { UserService } from "@/services/user.service";

const userService = new UserService();

function HomePage() {
  const navigate = useNavigate();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    userService.currentUser()
      .then((user) => {
        if (user?.id) {
          navigate("/create-workspace", { replace: true });
        }
      })
      .catch(() => {
        // Not authenticated
      })
      .finally(() => {
        setIsChecking(false);
      });
  }, [navigate]);

  if (isChecking) {
    return (
      <DefaultLayout>
        <div className="flex h-screen w-full items-center justify-center">
          <LogoSpinner />
        </div>
      </DefaultLayout>
    );
  }

  return (
    <DefaultLayout>
      <AuthenticationWrapper pageType={EPageTypes.NON_AUTHENTICATED}>
        <AuthBase authType={EAuthModes.SIGN_IN} />
      </AuthenticationWrapper>
    </DefaultLayout>
  );
}

export default HomePage;
