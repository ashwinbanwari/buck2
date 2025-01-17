/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under both the MIT license found in the
 * LICENSE-MIT file in the root directory of this source tree and the Apache
 * License, Version 2.0 found in the LICENSE-APACHE file in the root directory
 * of this source tree.
 */

use std::convert::Infallible;
use std::ops::FromResidual;

use crate::invocation_paths::InvocationPaths;

#[derive(Clone)]
pub enum InvocationPathsResult {
    OtherError(buck2_error::Error),
    Paths(InvocationPaths),
    OutsideOfRepo(buck2_error::Error), // this error ignored for creating invocation record for log commands
}

impl InvocationPathsResult {
    pub fn get_result(self) -> anyhow::Result<InvocationPaths> {
        match self {
            InvocationPathsResult::OtherError(e) => Err(e.into()),
            InvocationPathsResult::Paths(paths) => Ok(paths),
            InvocationPathsResult::OutsideOfRepo(e) => Err(e.into()),
        }
    }
}

impl<E: Into<::buck2_error::Error>> FromResidual<Result<Infallible, E>> for InvocationPathsResult {
    #[track_caller]
    fn from_residual(residual: Result<Infallible, E>) -> InvocationPathsResult {
        match residual {
            Ok(infallible) => match infallible {},
            // E -> buck2_error::Error -> InvocationPathsResult
            Err(e) => InvocationPathsResult::OtherError(e.into()),
        }
    }
}
